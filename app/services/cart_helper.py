import asyncio
from app.dao.user_dao import get_user_checkout


async def get_active_checkout_id(agent_user_id: int) -> str:
    """
    获取当前登录用户 active 状态购物车的 Saleor checkout_id。

    工具里不接收外部传入的 checkout_id，统一从这里按登录用户推导，
    避免用户操作到别人的购物车。
    """
    cart = await asyncio.to_thread(get_user_checkout, agent_user_id)
    if not cart:
        raise RuntimeError("当前用户还没有购物车，请先调用 create_cart 创建购物车")
    return cart["checkout_id"]


async def ensure_active_checkout_id(agent_user_id: int, saleor_user_id: str) -> str:
    """
    获取当前用户的购物车；不存在或已过期时自动创建/替换。

    用于“加购”这类用户已经明确表示要操作的场景，
    避免因为用户第一次加购没有购物车、或旧 checkout 过期，
    导致整个对话流中断。
    """
    # 延迟导入，避免工具模块之间的循环依赖
    from app.tools.shopping_tool.create_checkout import create_checkout

    # create_checkout 内部会：
    # 1. 查询 active 购物车；
    # 2. 检查 Saleor 中是否仍然存在；
    # 3. 存在则复用，不存在则删除旧绑定并创建新 checkout。
    result = await create_checkout(agent_user_id, saleor_user_id)
    checkout_id = (result or {}).get("checkout_id")

    if not checkout_id:
        raise RuntimeError("创建购物车失败，请稍后重试")

    return checkout_id