from starlette.responses import StreamingResponse
from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field, BaseModel
from pydantic import EmailStr
from app.services.saleor_client import SaleorClient
from app.services.users_service import password_login, register
from app.core.security import create_token, get_current_user
from app.core.security import token_check
from app.services.send_email_code import send_email_code
from app.services.verification_code import VerificationCodeService
import asyncio
from datetime import datetime



# 子路由
users_router = APIRouter()


class Login(BaseModel):
    email: EmailStr = Field(..., description="邮箱号")
    password: str = Field(..., description="密码")

class RegisterCode(BaseModel):
    email: EmailStr = Field(..., description="邮箱号")

class Register(BaseModel):
    email: EmailStr = Field(..., description="邮箱号")
    password: str = Field(..., description="密码")
    nickname: str = Field(..., description="用户昵称")
    code: str = Field(..., min_length=6, max_length=6, description="验证码")

class UserInfo(BaseModel):
    id: int
    saleor_user_id: str
    email: str
    role: str
    created_at: datetime

class UserInfoResponse(BaseModel):
    code: int
    msg: str
    data: UserInfo



@users_router.post("/login")
async def login_user(user: Login):
    result = await password_login(user.email, user.password)
    # 登录成功
    if result["code"] == 200:
        # 生成token
        token = create_token({"sub": str(result["user"]["id"]),
                              "saleor_user_id": result["user"]["saleor_user_id"],
                              "email": result["user"]["email"]
                              })
        result["data"] = token
    return result

@users_router.post("/register")
async def register_user(user: Register):
    result = await register(
        email=user.email,
        password=user.password,
        nickname=user.nickname,
        code=user.code
    )

    if result["code"] != 200:
        raise HTTPException(
            status_code=result["code"],
            detail=result["msg"]
        )

    return result

@users_router.post("/registerCode")
async def register_code(email: RegisterCode):
    # 检查邮箱是否已经注册
    client = SaleorClient()
    try:
        exists = await client.check_user_exists(email.email)
    finally:
        await client.close()

    if exists:
        raise HTTPException(
            status_code=409,
            detail="该邮箱已经注册"
        )

    # 初始化验证码服务
    code_service = VerificationCodeService()
    # 检查60秒发送限制
    if not code_service.set_send_limit(email.email, "register", 60):
        raise HTTPException(
            status_code=429,
            detail="验证码发送过于频繁，请稍后再试"
        )

    # 生成验证码并保存到 Redis
    code = code_service.create_code()
    code_service.save_code(
        email.email,
        code,
        "register",
        expire=60
    )
    try:
        await asyncio.to_thread(
            send_email_code,
            email.email,
            code
        )

    except Exception:
        # 邮件发送失败，清除验证码和发送限制
        code_service.delete_code(email.email, "register")
        code_service.delete_send_limit(email.email, "register")

        raise HTTPException(
            status_code=500,
            detail="验证码发送失败，请稍后重试"
        )
    return {
                "code": 200,
                "msg": "验证码已发送",
                "data": None
            }

@users_router.get("/me", response_model=UserInfoResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
        获取当前登录用户的信息
    """
    return {
        "code": 200,
        "msg": "获取用户信息成功",
        "data": {
            "id": current_user["agent_user_id"],
            "saleor_user_id": current_user["saleor_user_id"],
            "email": current_user["email"],
            "role": current_user["role"],
            "created_at": current_user["created_at"]
        }
    }

@users_router.get("/test")
async def admin_test(
    current_user: dict = Depends(token_check("admin"))
):
    return {
        "code": 200,
        "msg": "管理员权限验证成功",
        "data": {
            "user_id": current_user["agent_user_id"],
            "role": current_user["role"]
        }
    }