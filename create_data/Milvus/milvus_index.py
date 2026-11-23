import json
import re
import time
from typing import Any

from app.core.config import settings
from app.services.saleor_client import SaleorClient
from app.core.load_milvus_conn import LoadMilvusConn
from create_data.Milvus.milvus import (
    COLLECTION,
    ensure_collection,
    flush_collection,
    get_client,
)

PRODUCT_QUERY = """
query GetProductsForIndex(
    $first: Int!,
    $after: String,
    $channel: String!
) {
    products(first: $first, after: $after, channel: $channel) {
        pageInfo {
            hasNextPage
            endCursor
        }
        edges {
            node {
                id
                name
                slug
                description
                updatedAt
                productType { name }
                category { name }
                thumbnail { url }
                pricing {
                    priceRange {
                        start { gross { amount currency } }
                        stop  { gross { amount currency } }
                    }
                }
                variants {
                    id
                    name
                    sku
                    pricing {
                        price { gross { amount currency } }
                    }
                }
            }
        }
    }
}
"""


def plain_description(raw: str | None) -> str:
    if not raw:
        return ""
    try:
        data = json.loads(raw)
        parts = []
        for block in data.get("blocks", []):
            text = block.get("data", {}).get("text", "")
            parts.append(re.sub(r"<[^>]+>", "", text))
        return " ".join(parts).strip()
    except Exception:
        return str(raw)


async def fetch_all_products(channel: str) -> list[dict[str, Any]]:
    client = SaleorClient()
    nodes = []
    after = None
    try:
        while True:
            data = await client.execute(
                PRODUCT_QUERY,
                {"first": 100, "after": after, "channel": channel},
            )
            products = data.get("products") or {}
            for edge in products.get("edges") or []:
                nodes.append(edge["node"])
            page = products.get("pageInfo") or {}
            if not page.get("hasNextPage"):
                break
            after = page.get("endCursor")
        return nodes
    finally:
        await client.close()


def build_product_doc(node: dict[str, Any], channel: str) -> tuple[str, dict]:
    pricing = ((node.get("pricing") or {}).get("priceRange") or {})
    start = (pricing.get("start") or {}).get("gross") or {}
    stop = (pricing.get("stop") or {}).get("gross") or {}

    variants = []
    for variant in node.get("variants") or []:
        price = (
            ((variant.get("pricing") or {}).get("price") or {}).get("gross")
            or {}
        )
        variants.append({
            "id": variant.get("id"),
            "name": variant.get("name"),
            "sku": variant.get("sku"),
            "price": {
                "amount": price.get("amount"),
                "currency": price.get("currency"),
            },
        })

    name = node.get("name") or ""
    product_type = (node.get("productType") or {}).get("name") or ""
    category = (node.get("category") or {}).get("name") or ""
    description = plain_description(node.get("description"))

    text = "\n".join(
        part for part in [
            name,
            f"类型：{product_type}" if product_type else "",
            f"类目：{category}" if category else "",
            description,
            "规格：" + "、".join(
                str(v.get("name")) for v in variants if v.get("name")
            ) if variants else "",
        ] if part
    )

    row = {
        "id": f"{channel}:{node['id']}",
        "product_id": node["id"],
        "channel": channel,
        "name": name[:500],
        "description": description[:2000],
        "category": category[:250],
        "product_type": product_type[:250],
        "brand": "",
        "price_min": float(start.get("amount") or 0),
        "price_max": float(stop.get("amount") or 0),
        "currency": start.get("currency") or "USD",
        "image_url": ((node.get("thumbnail") or {}).get("url") or "")[:1000],
        "variants_json": variants,
        "updated_at": int(time.time()),
        "is_active": True,
    }

    return text, row


async def sync_products(channel: str | None = None) -> int:
    channel = channel or settings.saleor_channel
    nodes = await fetch_all_products(channel)

    texts, rows = [], []
    for node in nodes:
        text, row = build_product_doc(node, channel)
        texts.append(text)
        rows.append(row)

    vectors = LoadMilvusConn.embed_documents(texts)
    for row, vector in zip(rows, vectors):
        row["embedding"] = vector

    client = get_client()
    ensure_collection(client)

    # 批量 upsert，幂等
    for i in range(0, len(rows), 100):
        client.upsert(COLLECTION, rows[i:i + 100])

    flush_collection(client)
    return len(rows)


if __name__ == "__main__":
    import asyncio

    print("INDEXED:", asyncio.run(sync_products()))
