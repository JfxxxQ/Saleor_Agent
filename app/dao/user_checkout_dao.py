from app.core.load_mysql_conn import LoadMySQLConn

"""
    绑定购物车与用户的关系
"""


def bind_user_checkout(
    agent_user_id: int,
    saleor_user_id: str,
    checkout_id: str
):
    """
    绑定用户与 Saleor checkout。

    user_checkouts 上有 uk_agent_user_id 唯一索引，所以用 upsert：
    - 用户第一次创建购物车：插入新行；
    - 用户已有 completed/abandoned 的旧行：复用该行，切换到新的 checkout。
    """
    with LoadMySQLConn.get_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO user_checkouts
                (agent_user_id, saleor_user_id, checkout_id, status)
            VALUES (%s, %s, %s, 'active')
            ON DUPLICATE KEY UPDATE
                saleor_user_id = %s,
                checkout_id = %s,
                status = 'active'
            """,
            (
                agent_user_id,
                saleor_user_id,
                checkout_id,
                saleor_user_id,
                checkout_id,
            )
        )
        return cursor.lastrowid


# 根据 Agent 用户 ID 删除购物车关联记录
def delete_user_checkout(agent_user_id: int):
    with LoadMySQLConn.get_cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM user_checkouts
            WHERE agent_user_id = %s
            """,
            (agent_user_id,)
        )
        return cursor.rowcount

def complete_user_checkout(agent_user_id: int):
    """下单成功后，把当前 active 购物车标记为 completed"""
    with LoadMySQLConn.get_cursor() as cursor:
        cursor.execute(
            """
            UPDATE user_checkouts
            SET status = 'completed'
            WHERE agent_user_id = %s AND status = 'active'
            """,
            (agent_user_id,)
        )
        return cursor.rowcount