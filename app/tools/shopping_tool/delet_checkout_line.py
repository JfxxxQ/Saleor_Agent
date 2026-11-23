from langchain.tools import tool, ToolRuntime
from pydantic import BaseModel, Field
from app.agent.context import AgentContext
from app.services.cart_helper import get_active_checkout_id
from app.services.saleor_client import SaleorClient


class DeleteCheckoutLine(BaseModel):
    line_id: str = Field(..., description="购物车行的 ID，来自购物车信息中的 line_id")


@tool(args_schema=DeleteCheckoutLine)
async def delete_checkout_line(
    runtime: ToolRuntime[AgentContext],
    line_id: str,
) -> dict:
    """从当前登录用户的购物车中删除一行商品"""
    checkout_id = await get_active_checkout_id(runtime.context.agent_user_id)

    query = """
    mutation DeleteCheckoutLines(
        $checkoutId: ID!,
        $lines: [ID!]!
    ) {
        checkoutLinesDelete(
            id: $checkoutId,
            linesIds: $lines
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
        "lines": [line_id],
    }

    client = SaleorClient()
    try:
        data = await client.execute(query, variables)
        result = data.get("checkoutLinesDelete") or {}
        errors = result.get("errors") or []

        if errors:
            raise RuntimeError(f"删除商品失败：{errors}")

        checkout = result.get("checkout")
        if not checkout:
            raise RuntimeError("删除商品失败，未返回购物车信息")

        return checkout
    finally:
        await client.close()