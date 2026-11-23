from app.dao import history_dao

# 查询历史记录菜单
def query_history_menu(agent_user_id):
    results = history_dao.query_history_menu(agent_user_id)
    # 存储历史记录的列表
    data = []
    for item in results:
        created = item.get("created_at")
        data.append({
            "history_id": item["history_id"],
            "question": item.get("question"),
            "answer": item.get("answer"),
            "createTime": (
                created.strftime("%Y-%m-%d %H:%M:%S")
                if created else None
            ),
        })

    return {
        "code": 200,
        "msg": "查询成功",
        "data": data
    }

# 根据会话id查询完整历史对话记录
def query_history_list(agent_user_id, history_id):
    results = history_dao.query_history_list(agent_user_id, history_id)
    data = []
    for item in results:
        if item.get("question"):
            data.append({"role": "user", "content": item["question"]})
        if item.get("answer"):
            data.append({"role": "assistant", "content": item["answer"]})
    return {
        "code": 200,
        "msg": "查询成功",
        "data": data
    }

# 保存对话结果
def save_chat_result(agent_user_id, question, answer, parent_id="0"):
    new_id = history_dao.save_chat_result(
        agent_user_id, question, answer, parent_id
    )

    if new_id:
        return {
            "code": 200,
            "msg": "保存成功",
            "data": new_id
        }

    return {
        "code": 500,
        "msg": "保存失败",
        "data": None
    }

# 删除历史记录
def delete_history(agent_user_id, history_id):
    rowcount = history_dao.delete_history(agent_user_id, history_id)

    if rowcount > 0:
        return {
            "code": 200,
            "msg": "删除成功",
            "data": rowcount
        }

    return {
        "code": 500,
        "msg": "删除失败",
        "data": None
    }


