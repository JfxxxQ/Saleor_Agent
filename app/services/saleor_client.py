import json

import httpx
import asyncio
from typing import Any, Optional
from app.core.config import settings


class SaleorClient:
    """Saleor GraphQL API 客户端"""

    def __init__(self):
        self.api_url = settings.saleor_api_url
        self.token = settings.saleor_token

        self.client = httpx.AsyncClient(
            timeout=30.0
        )

    # 执行 GraphQL 查询
    async def execute(
        self,
        query: str,
        variables: Optional[dict[str, Any]] = None,
        user_token: Optional[str] = None
    ) -> dict[str, Any]:
        """
        通用 GraphQL 请求方法
        """

        headers = {
            "Content-Type": "application/json"
        }
        token = user_token or self.token

        # 如果配置了 Token，则添加认证信息
        if token:
            headers["Authorization"] = f"Bearer {token}"

        payload = {
            "query": query,
            "variables": variables or {}
        }

        try:
            response = await self.client.post(
                self.api_url,
                json=payload,
                headers=headers
            )

            response.raise_for_status()

            result = response.json()

            # GraphQL 可能在 HTTP 200 时仍然返回 errors
            if result.get("errors"):
                raise RuntimeError(
                    f"GraphQL 查询失败: {result['errors']}"
                )

            return result.get("data", {})

        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Saleor HTTP 请求失败: "
                f"{exc.response.status_code}, "
                f"{exc.response.text}"
            ) from exc

        except httpx.RequestError as exc:
            raise RuntimeError(
                f"无法连接 Saleor API: {exc}"
            ) from exc

    # 关闭 HTTP 客户端
    async def close(self):
        """关闭 HTTP 客户端"""
        await self.client.aclose()

    # 检查用户邮箱是否已经注册
    async def check_user_exists(self, email: str) -> bool:
        """
        根据邮箱检查 Saleor 中是否已经存在用户
        """

        query = """
        query CheckCustomerExists($email: String!) {
            customers(first: 1, search: $email) {
                edges {
                    node {
                        id
                        email
                    }
                }
            }
        }
        """

        variables = {
            "email": email
        }

        data = await self.execute(query, variables)

        customers = data["customers"]["edges"]

        # 精确比较邮箱，避免模糊搜索造成误判
        for edge in customers:
            customer_email = edge["node"]["email"]

            if customer_email and customer_email.lower() == email.lower():
                return True
        # 用户不存在
        return False

    # 注册账号
    async def account_register(
            self,
            email: str,
            password: str
    ) -> dict:
        query = """
        mutation AccountRegister(
            $email: String!
            $password: String!
        ) {
            accountRegister(
                input: {
                    email: $email
                    password: $password
                }
            ) {
                requiresConfirmation
                user {
                    id
                    email
                    firstName
                    lastName
                    isActive
                }
                errors {
                    field
                    message
                    code
                }
            }
        }
        """

        variables = {
            "email": email,
            "password": password
        }

        data = await self.execute(query, variables)

        return data["accountRegister"]

    # 用户登录
    async def login(self, email: str, password: str) -> dict:
        """
        调用 Saleor tokenCreate 验证用户账号密码
        """

        query = """
        mutation TokenCreate($email: String!, $password: String!) {
            tokenCreate(email: $email, password: $password) {
                token
                user {
                    id
                    email
                }
                errors {
                    field
                    message
                    code
                }
            }
        }
        """

        variables = {
            "email": email,
            "password": password
        }

        data = await self.execute(query, variables)

        return data["tokenCreate"]

    # 更新用户信息
    async def account_update(
        self,
        nickname: str,
        user_token: str
    ) -> dict:
        query = """
        mutation AccountUpdate($input: AccountInput!) {
            accountUpdate(input: $input) {
                user {
                    id
                    email
                    firstName
                    lastName
                }
                errors {
                    field
                    message
                    code
                }
            }
        }
        """

        variables = {
            "input": {
                "firstName": nickname[0],
                "lastName": nickname[1:]
            }
        }

        data = await self.execute(
            query,
            variables,
            user_token=user_token
        )

        return data["accountUpdate"]



if __name__ == "__main__":
    async def test():
        client = SaleorClient()
        try:
            result = await client.check_user_exists(
                "test@example.com",
            )
            print(json.dumps(result, indent=4, ensure_ascii=False))
        finally:
            await client.close()

    asyncio.run(test())
