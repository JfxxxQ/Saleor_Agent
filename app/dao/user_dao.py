from app.core.load_mysql_conn import LoadMySQLConn
import pymysql

# 根据 Saleor 用户 ID 查询 Agent 用户
def get_user_by_saleor_id(saleor_user_id: str):
    with LoadMySQLConn.get_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, saleor_user_id, role, created_at, updated_at
            FROM agent_users
            WHERE saleor_user_id = %s
            """,
            (saleor_user_id,),
        )
        return cursor.fetchone()

# 根据用户 ID 查询用户
def get_user_by_id(user_id: int):
    with LoadMySQLConn.get_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, saleor_user_id, role, created_at, updated_at
            FROM agent_users
            WHERE id = %s
            """,
            (user_id,),
        )
        return cursor.fetchone()

# 根据 Agent 用户 ID 查询购物车记录
def get_user_checkouts(agent_user_id: int):
    with LoadMySQLConn.get_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, agent_user_id, saleor_user_id, checkout_id
            FROM user_checkouts
            WHERE agent_user_id = %s
            """,
            (agent_user_id,)
        )
        return cursor.fetchall()

# 根据 Agent 用户 ID 获取一个购物车
def get_user_checkout(agent_user_id: int):
    with LoadMySQLConn.get_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, agent_user_id, saleor_user_id, checkout_id
            FROM user_checkouts
            WHERE agent_user_id = %s AND status = 'active'
            LIMIT 1
            """,
            (agent_user_id,)
        )
        return cursor.fetchone()

# 根据 Saleor Checkout ID 查询所属用户
def get_checkout_owner(checkout_id: str):
    with LoadMySQLConn.get_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, agent_user_id, saleor_user_id, checkout_id
            FROM user_checkouts
            WHERE checkout_id = %s AND status = 'active'
            """,
            (checkout_id,)
        )
        return cursor.fetchone()


# 如果用户不存在，则自动创建普通用户
def get_or_create_user(saleor_user_id: str):
    if not saleor_user_id:
        raise ValueError("saleor_user_id 不能为空")

    # 1. 先查，命中就直接返回，不产生任何 INSERT，也就不消耗自增 ID
    user = get_user_by_saleor_id(saleor_user_id)
    if user is not None:
        return user

    # 2. 不存在才插入
    try:
        with LoadMySQLConn.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO agent_users (saleor_user_id) VALUES (%s)",
                (saleor_user_id,),
            )
    except pymysql.err.IntegrityError as exc:
        # 1062 = Duplicate entry：并发请求抢先插入了，忽略即可
        if exc.args[0] != 1062:
            raise

    # 3. 重新查一次（新连接、新事务，确保能看到并发插入的行）
    return get_user_by_saleor_id(saleor_user_id)

if __name__ == "__main__":
    print(get_or_create_user("test_saleor_user_006"))
