from typing import Any

from app.services.cart_helper import ensure_active_checkout_id
from app.services.saleor_client import SaleorClient


ADD_CHECKOUT_LINES = """
mutation AddCheckoutLines(
    $checkoutId: ID!,
    $lines: [CheckoutLineInput!]!
) {
    checkoutLinesAdd(
        id: $checkoutId,
        lines: $lines
    ) {
        checkout {
            id
            quantity
            lines {
                id
                quantity
                variant {
                    id
                    name
                    product {
                        id
                        name
                    }
                }
            }
        }
        errors {
            field
            code
            message
        }
    }
}
"""


class CartServiceError(Exception):
    """购物车业务错误，可直接返回给前端提示。"""


async def add_checkout_line(
    agent_user_id: int,
    saleor_user_id: str,
    variant_id: str,
    quantity: int = 1,
) -> dict[str, Any]:
    """
    直接给当前用户加购，不经过大模型。

    卡片上的“加入购物车”按钮和聊天里的加购工具都复用这个函数。
    """
    if not variant_id:
        raise CartServiceError("缺少商品规格 ID")

    if quantity < 1 or quantity > 99:
        raise CartServiceError("商品数量必须在 1–99 之间")

    checkout_id = await ensure_active_checkout_id(
        agent_user_id,
        saleor_user_id,
    )

    client = SaleorClient()
    try:
        data = await client.execute(
            ADD_CHECKOUT_LINES,
            {
                "checkoutId": checkout_id,
                "lines": [
                    {
                        "variantId": variant_id,
                        "quantity": quantity,
                    }
                ],
            },
        )

        result = data.get("checkoutLinesAdd") or {}
        errors = result.get("errors") or []

        if errors:
            message = "; ".join(
                error.get("message")
                or error.get("code")
                or "加入购物车失败"
                for error in errors
            )
            raise CartServiceError(message)

        checkout = result.get("checkout")
        if not checkout:
            raise CartServiceError("加入购物车失败，未返回购物车信息")

        return checkout
    finally:
        await client.close()