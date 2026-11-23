from langchain.tools import tool, ToolRuntime
from pydantic import BaseModel, Field
from app.agent.context import AgentContext
from app.services.cart_helper import get_active_checkout_id
from app.services.saleor_client import SaleorClient


class SelectShippingMethod(BaseModel):
    method_id: str = Field(..., description="配送方式 ID，必须来自 get_shipping_methods 的返回结果",)

@tool(args_schema=SelectShippingMethod)
async def select_shipping_method(
    runtime: ToolRuntime[AgentContext],
    method_id: str,
) -> dict:
    """为当前登录用户的购物车选择配送方式"""
    checkout_id = await get_active_checkout_id(runtime.context.agent_user_id)

    query = """
    mutation UpdateCheckoutDeliveryMethod(
        $checkoutId: ID!,
        $methodId: ID!
    ) {
        checkoutDeliveryMethodUpdate(
            id: $checkoutId,
            deliveryMethodId: $methodId
        ) {
            checkout {
                id
                delivery {
                    id
                    shippingMethod {
                        id
                        name
                    }
                }
                shippingPrice {
                    gross {
                        amount
                        currency
                    }
                }
                totalPrice {
                    gross {
                        amount
                        currency
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
        "methodId": method_id,
    }

    client = SaleorClient()
    try:
        data = await client.execute(query, variables)
        result = data.get("checkoutDeliveryMethodUpdate") or {}
        errors = result.get("errors") or []

        if errors:
            raise RuntimeError(f"选择配送方式失败：{errors}")

        checkout = result.get("checkout")
        if not checkout:
            raise RuntimeError("选择配送方式失败，未返回购物车信息")

        return checkout
    finally:
        await client.close()