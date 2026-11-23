from app.core.config import settings
from app.services.saleor_client import SaleorClient
from app.dao.user_dao import get_user_checkout
from app.dao.user_checkout_dao import bind_user_checkout, delete_user_checkout
from app.agent.context import AgentContext
from langchain.tools import tool, ToolRuntime
import json
import asyncio



async def create_checkout(
    agent_user_id: int,
    saleor_user_id: str
):
    """创建一个空购物车"""
    # 查询用户是否已有购物车
    existing_checkout = await asyncio.to_thread(
        get_user_checkout,
        agent_user_id
    )
    # 如果已有购物车，直接返回
    if existing_checkout:
        checkout = await check_checkout_exists(
            existing_checkout["checkout_id"]
        )
        # Saleor 中购物车仍然存在，直接复用
        if checkout:
            return {
                "checkout_id": checkout["id"],
                "created": False,
                "message": "已获取现有购物车"
            }
        # Saleor 中购物车不存在，删除 MySQL 中的旧绑定
        await asyncio.to_thread(
            delete_user_checkout,
            agent_user_id
        )

    # 没有购物车，调用 Saleor 创建
    query = """
    mutation CreateCheckout($input: CheckoutCreateInput!) {
        checkoutCreate(input: $input) {
            checkout {
                id
                token
                quantity
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
        "input": {
            "channel": settings.saleor_channel,
            "lines": []
        }
    }
    client = SaleorClient()
    try:
        data = await client.execute(query, variables)
        result = data.get("checkoutCreate", {})
        # 处理业务层错误
        errors = result.get("errors", [])
        if errors:
            raise RuntimeError(
                f"创建购物车失败：{errors}"
            )
        checkout = result.get("checkout")
        if not checkout:
            raise RuntimeError("创建购物车失败，未返回 Checkout")

        # 4. 保存购物车与用户的关联关系
        await asyncio.to_thread(
            bind_user_checkout,
            agent_user_id,
            saleor_user_id,
            checkout["id"]
        )

        return {
            "checkout_id": checkout["id"],
            "created": True,
            "message": "购物车创建成功"
        }

    finally:
        await client.close()


@tool
async def create_cart(runtime: ToolRuntime[AgentContext]) -> dict:
    """为当前登录用户创建购物车；如果已有可用购物车则直接复用"""
    ctx = runtime.context
    return await create_checkout(ctx.agent_user_id, ctx.saleor_user_id)


# 检查saleor购物车是否存在
async def check_checkout_exists(checkout_id: str):
    query = """
    query GetCheckout($id: ID!) {
        checkout(id: $id) {
            id
            token
            quantity
        }
    }
    """

    client = SaleorClient()

    try:
        data = await client.execute(
            query,
            {"id": checkout_id}
        )

        return data.get("checkout")

    finally:
        await client.close()

async def test():
    try:
        checkout_id = await create_checkout(32, "VXNlcjo0Nw==")

        print(json.dumps(
            checkout_id,
            ensure_ascii=False,
            indent=4
        ))

        print("\n请妥善保存 Checkout ID，后续添加商品时需要使用。")

    except Exception as e:
        print(f"购物车创建失败：{e}")

if __name__ == "__main__":
    asyncio.run(test())
