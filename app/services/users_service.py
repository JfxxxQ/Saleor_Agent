import asyncio
from fastapi import HTTPException
from app.services.saleor_client import SaleorClient
from app.dao.user_dao import get_or_create_user
from app.services.verification_code import VerificationCodeService


# 密码登录
async def password_login(email, password):
    client = SaleorClient()
    try:
        result = await client.login(email, password)

        errors = result.get("errors") or []

        if errors:
            raise HTTPException(
                status_code=401,
                detail="邮箱或密码错误"
            )

        user = result.get("user")

        if not result.get("token") or not user or not user.get("id"):
            raise HTTPException(
                status_code=401,
                detail="用户验证失败"
            )

        # 获取 Saleor 用户 ID
        saleor_user_id = user.get("id")

        # 查询或创建 Agent 用户
        agent_user = await asyncio.to_thread(
            get_or_create_user,
            saleor_user_id
        )

        if not agent_user or not agent_user.get("role"):
            raise HTTPException(
                status_code=500,
                detail="Agent 用户信息异常"
            )

        # 从 Mysql 获取可信角色
        role = agent_user["role"]

        return {
            "code": 200,
            "msg": "登录成功",
            "data":None,
            "user": {
                "saleor_user_id": user["id"],
                "role": role,
                "id": agent_user["id"],
                "email": user["email"]
            }
        }

    finally:
        await client.close()

# 注册账号
async def register(email, password, nickname, code):
    client = SaleorClient()
    code_service = VerificationCodeService()
    # 获取redis邮箱验证码
    if not code_service.get_code(email, "register"):
        return {
            "code": 500,
            "msg": "验证码已过期",
            "data": None
        }

    # 验证邮箱验证码
    if code_service.verify_code(email, code, "register"):
        try:
            # 注册 Saleor 用户
            register_result = await client.account_register(email, password)
            if register_result.get("errors"):
                return {
                    "code": 400,
                    "msg": register_result["errors"][0]["message"],
                    "data": None
                }
            if not register_result.get("user"):
                raise Exception("Saleor 用户创建失败")
            # 登录获取 Customer Token
            login_result = await client.login(email, password)
            if login_result.get("errors"):
                raise Exception(login_result["errors"])
            if not login_result.get("token"):
                raise Exception("获取用户 Token 失败")
            user_token = login_result["token"]
            # 更新用户昵称
            await client.account_update(nickname, user_token)
            return {
                "code": 200,
                "msg": "注册成功",
                "data": None
            }

        except Exception as e:
            print(f"注册失败: {e}")
            return {
                "code": 500,
                "msg": "注册失败",
                "data": None
            }
        finally:
            await client.close()

    return {
        "code": 500,
        "msg": "验证码错误",
        "data": None
    }

