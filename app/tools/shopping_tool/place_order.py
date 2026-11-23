import asyncio
from langchain.tools import tool, ToolRuntime
from pydantic import BaseModel, Field
from app.agent.context import AgentContext
from app.dao.user_checkout_dao import complete_user_checkout
from app.services.cart_helper import get_active_checkout_id
from app.services.saleor_client import SaleorClient


class PlaceOrderInput(BaseModel):
    confirm: bool = Field(default=False, description="用户明确确认下单后传 true；否则不要传 true")
    use_shipping_as_billing: bool = Field(default=True, description="账单地址是否使用收货地址；默认 true")


GET_CHECKOUT = """
query GetCheckoutForOrder($id: ID!) {
    checkout(id: $id) {
        id
        email
        isShippingRequired
        quantity

        lines {
            id
            quantity
            variant {
                id
                name
            }
            totalPrice {
                gross {
                    amount
                    currency
                }
            }
        }

        shippingAddress {
            firstName
            lastName
            companyName
            streetAddress1
            streetAddress2
            city
            cityArea
            postalCode
            countryArea
            phone
            country {
                code
            }
        }

        billingAddress {
            id
        }

        delivery {
            id
            shippingMethod {
                id
                name
            }
        }

        subtotalPrice {
            gross {
                amount
                currency
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

        authorizeStatus
        chargeStatus

        problems {
            __typename
        }
    }
}
"""

SET_BILLING_ADDRESS = """
mutation SetBillingAddress($id: ID!, $address: AddressInput!) {
    checkoutBillingAddressUpdate(
        checkoutId: $id
        billingAddress: $address
    ) {
        checkout {
            id
            billingAddress {
                id
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

COMPLETE_ORDER = """
mutation CompleteOrder($id: ID!) {
    checkoutComplete(id: $id) {
        order {
            id
            number
            status
            paymentStatus
            total {
                gross {
                    amount
                    currency
                }
            }
        }
        confirmationNeeded
        confirmationData
        errors {
            field
            code
            message
        }
    }
}
"""


def _money(taxed_money: dict | None) -> dict | None:
    if not taxed_money:
        return None
    gross = taxed_money.get("gross") or {}
    return {
        "amount": gross.get("amount"),
        "currency": gross.get("currency"),
    }


def _address_input(address: dict | None) -> dict | None:
    if not address:
        return None
    return {
        "firstName": address.get("firstName") or "",
        "lastName": address.get("lastName") or "",
        "companyName": address.get("companyName") or "",
        "streetAddress1": address.get("streetAddress1") or "",
        "streetAddress2": address.get("streetAddress2") or "",
        "city": address.get("city") or "",
        "cityArea": address.get("cityArea") or "",
        "postalCode": address.get("postalCode") or "",
        "country": (address.get("country") or {}).get("code"),
        "countryArea": address.get("countryArea") or "",
        "phone": address.get("phone") or "",
    }


def _checkout_summary(checkout: dict) -> dict:
    delivery = checkout.get("delivery") or {}
    method = delivery.get("shippingMethod") or {}
    return {
        "checkout_id": checkout.get("id"),
        "email": checkout.get("email"),
        "lines": [
            {
                "line_id": line.get("id"),
                "variant_id": (line.get("variant") or {}).get("id"),
                "name": (line.get("variant") or {}).get("name"),
                "quantity": line.get("quantity"),
                "line_total": _money(line.get("totalPrice")),
            }
            for line in checkout.get("lines") or []
        ],
        "subtotal": _money(checkout.get("subtotalPrice")),
        "shipping": _money(checkout.get("shippingPrice")),
        "total": _money(checkout.get("totalPrice")),
        "shipping_method": method.get("name"),
        "has_shipping_address": bool(checkout.get("shippingAddress")),
    }


def _check_prerequisites(checkout: dict) -> dict | None:
    if not checkout.get("lines"):
        return {
            "reason": "EMPTY_CART",
            "message": "购物车为空，无法提交订单",
        }

    if not checkout.get("email"):
        return {
            "reason": "MISSING_EMAIL",
            "message": "请先设置下单邮箱",
        }

    if checkout.get("isShippingRequired"):
        if not checkout.get("shippingAddress"):
            return {
                "reason": "MISSING_SHIPPING_ADDRESS",
                "message": "请先在平台填写收货地址",
            }
        if not checkout.get("delivery"):
            return {
                "reason": "MISSING_DELIVERY_METHOD",
                "message": "请先选择配送方式",
            }

    return None


def _map_errors(errors: list[dict]) -> dict:
    mapping = {
        "CHECKOUT_NOT_FULLY_PAID": (
            "PAYMENT_REQUIRED",
            "订单信息已完整，但尚未收到付款，需要完成支付后才能生成订单",
        ),
        "BILLING_ADDRESS_NOT_SET": (
            "MISSING_BILLING_ADDRESS",
            "请先在平台填写账单地址",
        ),
        "SHIPPING_ADDRESS_NOT_SET": (
            "MISSING_SHIPPING_ADDRESS",
            "请先在平台填写收货地址",
        ),
        "DELIVERY_METHOD_NOT_SET": (
            "MISSING_DELIVERY_METHOD",
            "请先选择配送方式",
        ),
        "EMAIL_NOT_SET": (
            "MISSING_EMAIL",
            "请先设置下单邮箱",
        ),
    }

    for error in errors:
        code = error.get("code")
        if code in mapping:
            reason, message = mapping[code]
            return {
                "success": False,
                "reason": reason,
                "message": message,
                "errors": errors,
            }

    return {
        "success": False,
        "reason": "CHECKOUT_FAILED",
        "message": "提交订单失败",
        "errors": errors,
    }


@tool(args_schema=PlaceOrderInput)
async def place_order(
    runtime: ToolRuntime[AgentContext],
    confirm: bool = False,
    use_shipping_as_billing: bool = True,
) -> dict:
    """
    提交当前登录用户的购物车订单。
    必须先在对话中让用户确认商品、数量、金额和地址，用户确认后再传 confirm=True。
    """
    agent_user_id = runtime.context.agent_user_id
    checkout_id = await get_active_checkout_id(agent_user_id)

    client = SaleorClient()
    try:
        data = await client.execute(GET_CHECKOUT, {"id": checkout_id})
        checkout = data.get("checkout")
        if not checkout:
            return {
                "success": False,
                "reason": "CART_EXPIRED",
                "message": "购物车不存在或已过期，请重新创建购物车",
            }

        # 1. 前置条件检查
        problem = _check_prerequisites(checkout)
        if problem:
            return {
                "success": False,
                **problem,
                "checkout_id": checkout_id,
                "summary": _checkout_summary(checkout),
            }

        # 2. 未确认时只返回订单摘要，不提交
        if not confirm:
            return {
                "success": False,
                "reason": "CONFIRMATION_REQUIRED",
                "message": (
                    "请先向用户复述商品、数量、金额、收货地址和配送方式，"
                    "用户明确确认后再调用 place_order(confirm=True)"
                ),
                "summary": _checkout_summary(checkout),
            }

        # 3. Saleor 提交订单要求账单地址；默认与收货地址相同
        if not checkout.get("billingAddress"):
            if not use_shipping_as_billing:
                return {
                    "success": False,
                    "reason": "MISSING_BILLING_ADDRESS",
                    "message": "请先在平台填写账单地址",
                    "checkout_id": checkout_id,
                }

            billing = _address_input(checkout.get("shippingAddress"))
            if not billing:
                return {
                    "success": False,
                    "reason": "MISSING_SHIPPING_ADDRESS",
                    "message": "请先在平台填写收货地址",
                    "checkout_id": checkout_id,
                }

            billing_data = await client.execute(
                SET_BILLING_ADDRESS,
                {"id": checkout_id, "address": billing},
            )
            billing_result = billing_data.get("checkoutBillingAddressUpdate") or {}
            billing_errors = billing_result.get("errors") or []
            if billing_errors:
                return {
                    "success": False,
                    "reason": "INVALID_BILLING_ADDRESS",
                    "message": "账单地址设置失败",
                    "errors": billing_errors,
                }

        # ============================================================
        # 4. 支付扩展点
        #
        # 你当前 Saleor 没有安装支付 App，checkoutComplete 会返回
        # CHECKOUT_NOT_FULLY_PAID。
        #
        # 接入支付 App 后，在这里调用：
        #   paymentGatewayInitialize
        #   transactionInitialize / transactionProcess
        # 确认 chargeStatus 为 FULL 后，再执行下面的 checkoutComplete。
        # ============================================================

        complete_data = await client.execute(COMPLETE_ORDER, {"id": checkout_id})
        complete_result = complete_data.get("checkoutComplete") or {}
        order = complete_result.get("order")
        errors = complete_result.get("errors") or []

        # 5. 成功生成订单
        if order:
            await asyncio.to_thread(complete_user_checkout, agent_user_id)
            return {
                "success": True,
                "order": {
                    "order_id": order.get("id"),
                    "order_number": order.get("number"),
                    "status": order.get("status"),
                    "payment_status": order.get("paymentStatus"),
                    "total": _money(order.get("total")),
                },
            }

        # 6. 支付需要额外确认
        if complete_result.get("confirmationNeeded"):
            return {
                "success": False,
                "reason": "PAYMENT_CONFIRMATION_REQUIRED",
                "message": "支付还需要额外确认，订单尚未生成",
                "checkout_id": checkout_id,
                "confirmation_data": complete_result.get("confirmationData"),
            }

        # 7. 业务错误映射
        return _map_errors(errors)

    finally:
        await client.close()
