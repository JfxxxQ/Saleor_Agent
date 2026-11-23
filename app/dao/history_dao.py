# 历史记录操作
from app.core.load_mysql_conn import LoadMySQLConn


# 查询历史记录菜单
def query_history_menu(agent_user_id):
    with LoadMySQLConn.get_cursor() as cursor:
        cursor.execute(
            """
            SELECT history_id, agent_user_id, parent_id,
                   question, answer, created_at
            FROM agent_conversations
            WHERE parent_id = '0' AND agent_user_id = %s
            ORDER BY created_at DESC
            """,
            (str(agent_user_id),),
        )
        return cursor.fetchall()

# 根据会话id查询完整历史对话记录
def query_history_list(agent_user_id, history_id):
    with LoadMySQLConn.get_cursor() as cursor:
        cursor.execute(
            """
            SELECT history_id, agent_user_id, parent_id,
                   question, answer, created_at
            FROM agent_conversations
            WHERE agent_user_id = %s
              AND (history_id = %s OR parent_id = %s)
            ORDER BY history_id ASC
            """,
            (str(agent_user_id), int(history_id), str(history_id)),
        )
        return cursor.fetchall()

# 保存对话结果
def save_chat_result(agent_user_id, question, answer, parent_id="0"):
    with LoadMySQLConn.get_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO agent_conversations
                (agent_user_id, parent_id, question, answer, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
            """,
            (str(agent_user_id), str(parent_id), question, answer),
        )
        return cursor.lastrowid


# 删除会话历史记录
def delete_history(agent_user_id, history_id):
    with LoadMySQLConn.get_cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM agent_conversations
            WHERE agent_user_id = %s
              AND (history_id = %s OR parent_id = %s)
            """,
            (str(agent_user_id), int(history_id), str(history_id)),
        )
        return cursor.rowcount

