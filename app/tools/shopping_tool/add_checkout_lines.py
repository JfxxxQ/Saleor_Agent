from langchain.tools import tool, ToolRuntime
from pydantic import BaseModel, Field

from app.agent.context import AgentContext
from app.services.cart_service import add_checkout_line


class AddCheckoutLines(BaseModel):
    variant_id: str = Field(..., description="商品规格 ID，必须来自商品查询结果")
    quantity: int = Field(..., ge=1, le=99, description="商品数量")


@tool(args_schema=AddCheckoutLines)
async def add_checkout_lines(
    runtime: ToolRuntime[AgentContext],
    variant_id: str,
    quantity: int,
) -> dict:
    """把指定规格的商品加入当前登录用户的购物车"""
    try:
        return await add_checkout_line(
            agent_user_id=runtime.context.agent_user_id,
            saleor_user_id=runtime.context.saleor_user_id,
            variant_id=variant_id,
            quantity=quantity,
        )
    except Exception as exc:
        # 不要让工具异常中断整个对话流，返回结构化错误给模型
        return {
            "success": False,
            "message": str(exc),
        }