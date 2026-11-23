from langchain.tools import tool, ToolRuntime
from app.agent.context import AgentContext
from app.services.cart_helper import get_active_checkout_id
from app.services.saleor_client import SaleorClient


@tool
async def get_checkout_summary(runtime: ToolRuntime[AgentContext]) -> dict:
    """获取当前登录用户购物车的完整信息：商品行、金额、地址和配送方式"""
    checkout_id = await get_active_checkout_id(runtime.context.agent_user_id)

    query = """
    query GetCheckoutSummary($checkoutId: ID!) {
        checkout(id: $checkoutId) {
            id
            email
            isShippingRequired

            lines {
                id
                quantity
                totalPrice {
                    gross {
                        amount
                        currency
                    }
                }
                variant {
                    id
                    name
                    sku
                    pricing {
                        price {
                            gross {
                                amount
                                currency
                            }
                        }
                        priceUndiscounted {
                            gross {
                                amount
                                currency
                            }
                        }
                    }
                    product {
                        id
                        name
                        slug
                    }
                }
            }

            shippingAddress {
                firstName
                lastName
                streetAddress1
                streetAddress2
                city
                countryArea
                postalCode
                phone
                country {
                    code
                    country
                }
            }

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

            subtotalPrice {
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

            problems {
                __typename
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
        return checkout
    finally:
        await client.close()