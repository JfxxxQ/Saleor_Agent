from app.pggresql_manager.pggresql_pool import pool

"""
摘要记忆，记忆对话的摘要记忆
"""
class SummaryMemory:

    def __init__(self):
        self.pool = pool
    #添加记忆
    def add_memory(self,history_id,summary):
      with self.pool.connection() as con:
          with con.cursor() as cursor:
              cursor.execute(
                  """
                  INSERT INTO conversation_summary (history_id, summary)
                  VALUES (%s, %s) ON CONFLICT (history_id) DO
                  UPDATE
                      SET summary = EXCLUDED.summary,
                      update_time = NOW()
                  """,
                  (str(history_id), str(summary)),
              )
              #事务提交
              con.commit()
    #查询记忆
    def load_memory(self,history_id):
        with self.pool.connection() as con:
            with con.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT summary
                    FROM conversation_summary
                    WHERE history_id = %s
                    """,
                    (str(history_id),),
                )
                row = cursor.fetchone()
                return row[0] if row else ""