from langchain.tools import tool, ToolRuntime
from app.agent.context import AgentContext
from app.services.cart_helper import get_active_checkout_id
from app.services.saleor_client import SaleorClient


@tool
async def get_shipping_methods(runtime: ToolRuntime[AgentContext]) -> dict:
    """查询当前购物车可用的配送方式。需要先设置收货地址，否则列表可能为空。"""
    checkout_id = await get_active_checkout_id(runtime.context.agent_user_id)

    query = """
    query GetCheckoutShippingMethods($checkoutId: ID!) {
        checkout(id: $checkoutId) {
            id
            shippingMethods {
                id
                name
                price {
                    amount
                    currency
                }
                minimumDeliveryDays
                maximumDeliveryDays
            }
        }
    }
    """

    client = SaleorClient()
    try:
        data = await client.execute(query, {"checkoutId": checkout_id})
        checkout = data.get("checkout")
        if not checkout:
            raise RuntimeError("购物车不存在或已过期，请重新调用 create_cart")

        methods = checkout.get("shippingMethods") or []
        result = {
            "checkout_id": checkout.get("id"),
            "shipping_methods": methods,
        }
        if not methods:
            result["message"] = "没有可用配送方式，请先设置收货地址"
        return result
    finally:
        await client.close()