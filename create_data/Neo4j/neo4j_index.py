import asyncio
import json
import re
from typing import Any

from app.core.config import settings
from app.core.load_neo4j_conn import LoadNeo4jConn
from create_data.Neo4j.neo4j_schema import ensure_schema
from app.services.saleor_client import SaleorClient


PRODUCT_QUERY = """
query GetProductsForGraph(
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

                productType {
                    id
                    name
                }

                category {
                    id
                    name
                    parent {
                        id
                        name
                    }
                }

                collections {
                    id
                    name
                }

                thumbnail {
                    url
                }

                attributes {
                    attribute {
                        id
                        name
                        slug
                    }
                    values {
                        id
                        name
                        slug
                    }
                }

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
                    attributes {
                        attribute {
                            id
                            name
                        }
                        values {
                            id
                            name
                        }
                    }
                    pricing {
                        price { gross { amount currency } }
                    }
                }
            }
        }
    }
}
"""

UPSERT_PRODUCTS = """
UNWIND $rows AS row
MERGE (p:Product {id: row.id})
SET p.name = row.name,
    p.slug = row.slug,
    p.description = row.description,
    p.price_min = row.price_min,
    p.price_max = row.price_max,
    p.currency = row.currency,
    p.image_url = row.image_url,
    p.is_active = true,
    p.updated_at = timestamp()

MERGE (t:ProductType {id: row.product_type_id})
SET t.name = row.product_type_name
MERGE (p)-[:HAS_TYPE]->(t)

MERGE (c:Category {id: row.category_id})
SET c.name = row.category_name
MERGE (p)-[:IN_CATEGORY]->(c)

FOREACH (_ IN CASE WHEN row.category_parent_id IS NULL THEN [] ELSE [1] END |
    MERGE (parent:Category {id: row.category_parent_id})
    SET parent.name = row.category_parent_name
    MERGE (c)-[:PARENT]->(parent)
)

FOREACH (attr IN row.attributes |
    MERGE (a:AttributeValue {key: attr.key, value: attr.value})
    MERGE (p)-[:HAS_ATTRIBUTE]->(a)
)

FOREACH (v IN row.variants |
    MERGE (variant:Variant {id: v.id})
    SET variant.name = v.name,
        variant.sku = v.sku,
        variant.price = v.price,
        variant.currency = v.currency
    MERGE (p)-[:HAS_VARIANT]->(variant)

    FOREACH (attr IN v.attributes |
        MERGE (va:AttributeValue {key: attr.key, value: attr.value})
        MERGE (variant)-[:HAS_ATTRIBUTE]->(va)
    )
)

FOREACH (col IN row.collections |
    MERGE (collection:Collection {id: col.id})
    SET collection.name = col.name
    MERGE (p)-[:IN_COLLECTION]->(collection)
)
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
    nodes: list[dict[str, Any]] = []
    after = None

    try:
        while True:
            data = await client.execute(
                PRODUCT_QUERY,
                {
                    "first": 100,
                    "after": after,
                    "channel": channel,
                },
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


def build_graph_row(node: dict[str, Any]) -> dict[str, Any]:
    pricing = ((node.get("pricing") or {}).get("priceRange") or {})
    start = (pricing.get("start") or {}).get("gross") or {}
    stop = (pricing.get("stop") or {}).get("gross") or {}

    category = node.get("category") or {}
    category_parent = category.get("parent") or {}

    product_type = node.get("productType") or {}
    description = plain_description(node.get("description"))

    attributes = []
    for item in node.get("attributes") or []:
        key = (item.get("attribute") or {}).get("name")
        if not key:
            continue
        for value in item.get("values") or []:
            value_name = value.get("name")
            if value_name:
                attributes.append({
                    "key": key,
                    "value": value_name,
                })

    variants = []
    for variant in node.get("variants") or []:
        price = (
            ((variant.get("pricing") or {}).get("price") or {})
            .get("gross") or {}
        )

        variant_attributes = []
        for item in variant.get("attributes") or []:
            key = (item.get("attribute") or {}).get("name")
            if not key:
                continue
            for value in item.get("values") or []:
                value_name = value.get("name")
                if value_name:
                    variant_attributes.append({
                        "key": key,
                        "value": value_name,
                    })

        variants.append({
            "id": variant.get("id"),
            "name": variant.get("name"),
            "sku": variant.get("sku"),
            "price": price.get("amount"),
            "currency": price.get("currency"),
            "attributes": variant_attributes,
        })

    collections = [
        {
            "id": collection.get("id"),
            "name": collection.get("name") or "",
        }
        for collection in node.get("collections") or []
        if collection.get("id")
    ]

    return {
        "id": node["id"],
        "name": node.get("name") or "",
        "slug": node.get("slug") or "",
        "description": description[:2000],
        "price_min": float(start.get("amount") or 0),
        "price_max": float(stop.get("amount") or 0),
        "currency": start.get("currency") or "USD",
        "image_url": ((node.get("thumbnail") or {}).get("url") or ""),
        "category_id": category.get("id") or "uncategorized",
        "category_name": category.get("name") or "Uncategorized",
        "category_parent_id": category_parent.get("id"),
        "category_parent_name": category_parent.get("name") or "",
        "product_type_id": product_type.get("id") or "unknown",
        "product_type_name": product_type.get("name") or "Unknown",
        "attributes": attributes,
        "variants": variants,
        "collections": collections,
    }


def write_rows_to_neo4j(rows: list[dict[str, Any]]):
    ensure_schema()

    driver = LoadNeo4jConn.get_driver()

    with driver.session(database=LoadNeo4jConn.database()) as session:
        # 先全部标记为不活跃，后面的 upsert 会重新激活当前商品
        session.run(
            "MATCH (p:Product) SET p.is_active = false"
        ).consume()

        batch_size = 200
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            session.run(UPSERT_PRODUCTS, rows=batch).consume()


async def sync_products_to_neo4j() -> int:
    channel = settings.saleor_channel
    nodes = await fetch_all_products(channel)

    rows = [build_graph_row(node) for node in nodes]

    await asyncio.to_thread(write_rows_to_neo4j, rows)

    return len(rows)


if __name__ == "__main__":
    print("SYNCED:", asyncio.run(sync_products_to_neo4j()))
