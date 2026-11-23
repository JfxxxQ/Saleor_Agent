import pymysql
from app.core.config import settings
from contextlib import contextmanager



class LoadMySQLConn:
    def __init__(self):
        self.conn = self.load_mysql_conn()

    # 加载mysql连接
    @staticmethod
    def load_mysql_conn():
        return pymysql.connect(
            host=settings.mysql_host,
            port=int(settings.mysql_port),
            user=settings.mysql_user,
            password=settings.mysql_password,
            database=settings.mysql_database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
        )

    # 关闭mysql连接
    @staticmethod
    @contextmanager
    def get_cursor():
        conn = LoadMySQLConn.load_mysql_conn()
        cursor = conn.cursor()

        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()


