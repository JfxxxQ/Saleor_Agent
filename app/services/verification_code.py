import secrets
from app.core.load_redis_conn import LoadRedisConn



class VerificationCodeService:
    def __init__(self):
        self.redis_conn = LoadRedisConn.load_redis_conn()

    # =========================
    # 验证码
    # =========================

    # 生成验证码
    @staticmethod
    def create_code():
        return f"{secrets.randbelow(1000000):06d}"

    # 保存验证码，默认60秒过期
    def save_code(self,
                  email: str,
                  code: str,
                  purpose: str,
                  expire: int = 60):
        key = f"agent:{purpose}:code:{email}"
        self.redis_conn.set(key, code, ex=expire)

    # 获取redis中保存的验证码
    def get_code(self, email: str, purpose: str):
        key = f"agent:{purpose}:code:{email}"
        return self.redis_conn.get(key)

    # 删除redis中保存的验证码
    def delete_code(self, email: str, purpose: str):
        key = f"agent:{purpose}:code:{email}"
        self.redis_conn.delete(key)

    # 验证redis中的验证码
    def verify_code(self,
                    email: str,
                    code: str,
                    purpose: str
                    ) -> bool:
        redis_code = self.get_code(email, purpose)
        if redis_code is None:
            return False
        if redis_code != code:
            return False

        # 验证成功后立即删除
        self.delete_code(email, purpose)
        return True

    # =========================
    # 发送频率限制
    # =========================
    def set_send_limit(
            self,
            email: str,
            purpose: str,
            expire_seconds: int = 60,
    ) -> bool:

        key = f"agent:{purpose}:send:{email}"
        return bool(
            self.redis_conn.set(
                key,
                "1",
                ex=expire_seconds,
                nx=True,
            )
        )

    # 删除发送限制
    def delete_send_limit(self, email: str, purpose: str):
        key = f"agent:{purpose}:send:{email}"
        self.redis_conn.delete(key)
