import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.security import get_current_user
from app.services.cart_service import CartServiceError, add_checkout_line


cart_router = APIRouter()
logger = logging.getLogger(__name__)


class AddCartLine(BaseModel):
    variant_id: str = Field(..., min_length=1, description="商品规格 ID")
    quantity: int = Field(default=1, ge=1, le=99, description="商品数量")


@cart_router.post("/lines")
async def add_line(
    payload: AddCartLine,
    current_user: dict = Depends(get_current_user),
):
    """商品卡片直接加购，不经过 Agent。"""
    try:
        checkout = await add_checkout_line(
            agent_user_id=current_user["agent_user_id"],
            saleor_user_id=current_user["saleor_user_id"],
            variant_id=payload.variant_id,
            quantity=payload.quantity,
        )
    except CartServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        logger.exception("加入购物车失败")
        raise HTTPException(
            status_code=500,
            detail="加入购物车失败，请稍后重试",
        )

    return {
        "code": 200,
        "msg": "已加入购物车",
        "data": checkout,
    }