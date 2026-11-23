"""
    1、创建令牌
    2、验证令牌
"""
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from app.core.config import settings
from app.dao.user_dao import get_user_by_id
import asyncio


bearer_scheme = HTTPBearer(auto_error=False)

# 创建令牌
def create_token(
    data: dict,
) -> str:
    """
    :param data: 需要存入载荷的数据内容
    :return: 生成的token字符串
    """
    # 拷贝数据内容
    to_encode = data.copy()
    # 计算token多久过期 = 当前时间 + 过期时间
    expires_time = (
        datetime.now(timezone.utc) +
        timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )
    # 把过期时间存入载荷
    to_encode.update({"exp": expires_time, "iat": datetime.now(timezone.utc)})
    # 创建令牌
    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )


# 验证令牌
def verify_token(token: str) -> dict:
    """
    :param token: 需要验证的token字符串
    :return: 验证通过的载荷数据
    """
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        # 抛出没有token异常
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )


# 导入fastapi集成的OAuth2
"""
    能够解析客户端传过来的Authorization内容，自动在Authorization提取token字段
"""

# 获取当前用户的数据内容
from fastapi import Depends
async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="未提供认证信息"
        )

    # 验证 JWT
    token = credentials.credentials
    user_dict = verify_token(token)
    # 获取 Agent 用户 ID
    agent_user_id = user_dict.get("sub")
    if not agent_user_id:
        raise HTTPException(
            status_code=401,
            detail="无效的用户身份"
        )

    # 从 MySQL 查询用户最新信息
    agent_user = await asyncio.to_thread(
        get_user_by_id,
        agent_user_id
    )
    if not agent_user:
        raise HTTPException(
            status_code=403,
            detail="用户不存在"
        )
    if not agent_user.get("role"):
        raise HTTPException(
            status_code=403,
            detail="用户角色异常"
        )

    # 如果以后加了 is_active，这里一起判断
    # if not agent_user.get("is_active"):
    #     raise HTTPException(status_code=403, detail="用户已被禁用")

    return {
        "sub": str(agent_user["id"]),
        "saleor_user_id": agent_user["saleor_user_id"],
        "email": user_dict.get("email"),
        "agent_user_id": agent_user["id"],
        "role": agent_user["role"],  # 以数据库为准
        "created_at": agent_user.get("created_at"),
        "token_payload": user_dict,  # 需要看原始 claim 时用
    }


# token认证
def token_check(*roles: str):
    allowed = {r.strip().lower() for r in roles}
    def role_check(
            current_user: dict = Depends(get_current_user)
    ) -> dict:
        role = (current_user.get("role") or "").strip().lower()
        if role not in allowed:
            raise HTTPException(status_code=403, detail="权限不足")
        return current_user

    return role_check
