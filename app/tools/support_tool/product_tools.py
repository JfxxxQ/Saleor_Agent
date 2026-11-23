from typing import Any

from langchain.tools import ToolRuntime, tool
from pydantic import BaseModel, Field

from app.agent.context import AgentContext
from app.core.config import settings
from app.services.saleor_client import SaleorClient


CARD_LIMIT = 20

# Saleor 的搜索对 "t-shirt" 匹配很少；中文 T 恤统一拆成 tee + shirt 合并查询。
SEARCH_ALIASES = {
    "t-shirt": ["tee", "shirt"],
    "tshirt": ["tee", "shirt"],
    "t恤": ["tee", "shirt"],

    "果汁": ["juice"],
    "水果汁": ["juice"],
    "胡萝卜汁": ["carrot juice"],
    "苹果汁": ["apple juice"],
    "香蕉汁": ["banana juice"],
}


class Product(BaseModel):
    first: int = Field(default=100, description="查询商品数量")
    search: str | None = Field(
        default=None,
        description=(
            "英文商品关键词，如 tee、shirt、headphones。"
            "用户明确描述商品类别或用途时传关键词，系统会展示商品图片卡片；"
            "不传则只返回文字列表，不展示卡片。"
        ),
    )


def _search_terms(keyword: str | None) -> list[str | None]:
    if not keyword:
        return [None]

    key = keyword.strip().lower().replace(" ", "")
    return SEARCH_ALIASES.get(key, [keyword.strip()])


def _to_card(node: dict[str, Any]) -> dict[str, Any]:
    """把 Saleor 商品节点转换成前端商品卡片数据。"""
    pricing = node.get("pricing") or {}
    price_range = pricing.get("priceRange") or {}
    start = (price_range.get("start") or {}).get("gross") or {}
    stop = (price_range.get("stop") or {}).get("gross") or {}

    variants = []
    for variant in node.get("variants") or []:
        price = (
            ((variant.get("pricing") or {}).get("price") or {}).get("gross")
            or {}
        )
        variants.append(
            {
                "id": variant.get("id"),
                "name": variant.get("name"),
                "price": {
                    "amount": price.get("amount"),
                    "currency": price.get("currency"),
                },
            }
        )

    return {
        "id": node.get("id"),
        "name": node.get("name"),
        "image": (node.get("thumbnail") or {}).get("url"),
        "price": {
            "amount": start.get("amount"),
            "currency": start.get("currency"),
        },
        "price_max": {
            "amount": stop.get("amount"),
            "currency": stop.get("currency"),
        },
        "productType": (node.get("productType") or {}).get("name"),
        "variants": variants,
    }


@tool(args_schema=Product)
async def get_products(
    runtime: ToolRuntime[AgentContext],
    first: int = 100,
    search: str | None = None,
) -> list[dict[str, Any]]:
    """
    查询商品列表。

    传入 search 时，系统会给前端发送商品卡片事件；
    不传 search 时只返回文字列表，不展示卡片。
    """
    keyword = (search or "").strip() or None

    query = """
    query GetProducts($first: Int!, $channel: String!, $search: String) {
        products(
            first: $first
            channel: $channel
            filter: { search: $search }
        ) {
            edges {
                node {
                    id
                    name
                    slug
                    description

                    productType {
                        name
                    }

                    thumbnail {
                        url
                    }

                    category {
                        id
                        name
                    }

                    pricing {
                        priceRange {
                            start {
                                gross {
                                    amount
                                    currency
                                }
                                net {
                                    amount
                                    currency
                                }
                            }
                            stop {
                                gross {
                                    amount
                                    currency
                                }
                                net {
                                    amount
                                    currency
                                }
                            }
                        }
                    }

                    variants {
                        id
                        name
                        sku

                        pricing {
                            price {
                                gross {
                                    amount
                                    currency
                                }
                                net {
                                    amount
                                    currency
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    """

    client = SaleorClient()
    try:
        nodes: list[dict[str, Any]] = []
        seen_ids: set[str] = set()

        # 一个关键词可能查不全（如 t-shirt），按别名拆成多个查询并合并去重
        for term in _search_terms(keyword):
            variables = {
                "first": first,
                "channel": settings.saleor_channel,
                "search": term,
            }

            data = await client.execute(query, variables)
            edges = (data.get("products") or {}).get("edges") or []

            for edge in edges:
                node = edge["node"]
                node_id = node.get("id")
                if not node_id or node_id in seen_ids:
                    continue
                seen_ids.add(node_id)
                nodes.append(node)

        # 只有用户明确查询某类商品（传了 search）时才展示图片卡片
        if keyword:
            cards = [_to_card(node) for node in nodes]
            cards = [
                card
                for card in cards
                if card.get("id") and card.get("name")
            ]

            if cards:
                runtime.stream_writer(
                    {
                        "type": "products",
                        "items": cards[:CARD_LIMIT],
                    }
                )

        return nodes
    finally:
        await client.close()