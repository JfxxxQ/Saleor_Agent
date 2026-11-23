from langchain.tools import tool, ToolRuntime
from pydantic import BaseModel, Field
from app.agent.context import AgentContext
from app.services.cart_helper import get_active_checkout_id
from app.services.saleor_client import SaleorClient


class UpdateCheckoutLine(BaseModel):
    line_id: str = Field(..., description="购物车行的 ID，来自购物车信息中的 line_id")
    quantity: int = Field(..., ge=1, le=99, description="修改后的商品数量")


@tool(args_schema=UpdateCheckoutLine)
async def update_checkout_line(
    runtime: ToolRuntime[AgentContext],
    line_id: str,
    quantity: int,
) -> dict:
    """修改当前登录用户购物车中某一行的商品数量"""
    checkout_id = await get_active_checkout_id(runtime.context.agent_user_id)

    query = """
    mutation UpdateCheckoutLines(
        $checkoutId: ID!,
        $lines: [CheckoutLineUpdateInput!]!
    ) {
        checkoutLinesUpdate(
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

    variables = {
        "checkoutId": checkout_id,
        "lines": [
            {
                "lineId": line_id,
                "quantity": quantity,
            }
        ],
    }

    client = SaleorClient()
    try:
        data = await client.execute(query, variables)
        result = data.get("checkoutLinesUpdate") or {}
        errors = result.get("errors") or []

        if errors:
            raise RuntimeError(f"修改商品数量失败：{errors}")

        checkout = result.get("checkout")
        if not checkout:
            raise RuntimeError("修改商品数量失败，未返回购物车信息")

        return checkout
    finally:
        await client.close()