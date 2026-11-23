import redis
from app.core.config import settings

class LoadRedisConn:
    _client = None

    # 加载redis连接
    @classmethod
    def load_redis_conn(cls):
        if cls._client is None:
            cls._client = redis.Redis(
                host=settings.redis_host,
                port=int(settings.redis_port),
                db=int(settings.redis_db),
                decode_responses=True # 解码响应结果为字符串，否则是字节
            )
        return cls._client

    # 关闭redis连接
    @staticmethod
    def close_redis_conn(conn):
        conn.close()