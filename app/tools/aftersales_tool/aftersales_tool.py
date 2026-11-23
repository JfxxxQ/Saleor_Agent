import asyncio
import json
from typing import Any, Optional
from langchain.tools import tool
from pydantic import BaseModel, Field

from app.core.load_milvus_conn import LoadMilvusConn


COLLECTION = "aftersales"

OUTPUT_FIELDS = [
    "product_id",
    "product_name",
    "product_type",
    "category",
    "policy_type",
    "price_min",
    "price_max",
    "currency",
    "return_window",
    "return_policy",
    "return_shipping",
    "refund_method",
    "issue_solution",
    "remark",
]


class AfterSalesQueryInput(BaseModel):
    query: str = Field(
        ...,
        description="用户的售后问题，例如：这件T恤能退吗、果汁漏液了怎么办、礼品卡能退款吗",
    )
    product_id: Optional[str] = Field(
        default=None,
        description="可选，Saleor 商品 ID。已知具体商品时传入，可精确查询该商品的售后政策",
    )
    policy_type: Optional[str] = Field(
        default=None,
        description="可选政策类型：食品饮料、服饰、鞋类、配饰、眼镜/配饰、家居用品、数字商品、礼品卡/虚拟商品",
    )
    limit: int = Field(
        default=3,
        ge=1,
        le=10,
        description="返回条数，默认3条",
    )


def _search_aftersales(
    query: str,
    product_id: str | None = None,
    policy_type: str | None = None,
    limit: int = 3,
) -> list[dict[str, Any]]:
    client = LoadMilvusConn.load_milvus_conn()

    if not client.has_collection(COLLECTION):
        raise RuntimeError(f"Milvus 集合 {COLLECTION} 不存在，请先导入售后数据")

    # Milvus Lite 重新打开后 collection 可能是 released 状态
    client.load_collection(COLLECTION)

    filters = []
    if product_id:
        filters.append(f"product_id == {json.dumps(str(product_id), ensure_ascii=False)}")
    if policy_type:
        filters.append(f"policy_type == {json.dumps(str(policy_type), ensure_ascii=False)}")

    search_kwargs = {
        "collection_name": COLLECTION,
        "data": [LoadMilvusConn.embed_query(query)],
        "anns_field": "embedding",
        "search_params": {
            "metric_type": "COSINE",
            "params": {},
        },
        "limit": limit,
        "output_fields": OUTPUT_FIELDS,
    }
    if filters:
        search_kwargs["filter"] = " and ".join(filters)

    result = client.search(**search_kwargs)

    items = []
    for hits in result:
        for hit in hits:
            entity = hit.get("entity") or {}
            items.append({
                "score": hit.get("distance"),
                "product_id": entity.get("product_id"),
                "product_name": entity.get("product_name"),
                "product_type": entity.get("product_type"),
                "category": entity.get("category"),
                "policy_type": entity.get("policy_type"),
                "price_min": entity.get("price_min"),
                "price_max": entity.get("price_max"),
                "currency": entity.get("currency"),
                "return_window": entity.get("return_window"),
                "return_policy": entity.get("return_policy"),
                "return_shipping": entity.get("return_shipping"),
                "refund_method": entity.get("refund_method"),
                "issue_solution": entity.get("issue_solution"),
                "remark": entity.get("remark"),
            })

    return items


@tool(args_schema=AfterSalesQueryInput)
async def query_aftersales_policy(
    query: str,
    product_id: str | None = None,
    policy_type: str | None = None,
    limit: int = 3,
) -> list[dict[str, Any]]:
    """
    查询售后政策，包括退货时限、退货政策、退货运费、退款方式和商品问题解决方法。
    用户询问退货、退款、换货、商品质量问题、食品/数字商品/礼品卡售后时使用。
    """
    try:
        return await asyncio.to_thread(
            _search_aftersales,
            query,
            product_id,
            policy_type,
            limit,
        )
    except Exception as exc:
        return [{
            "success": False,
            "error": str(exc),
        }]
