from pydantic import Field, BaseModel
from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.services import history_service


history_router = APIRouter()

class History(BaseModel):
    question: str = Field(..., description="用户问题")
    answer: str = Field(..., description="AI回答")
    parent_id: str | int = Field(default="0", description="父会话ID；根会话传 0")

# 查询历史记录菜单
@history_router.get("/queryHistoryMenu")
def query_history_menu(current_user: dict = Depends(get_current_user)):
    return history_service.query_history_menu(current_user["agent_user_id"])

# 根据会话id查询完整历史对话记录
@history_router.get("/queryHistoryList/{history_id}")
def query_history_list(history_id: int, current_user: dict = Depends(get_current_user)):
    return history_service.query_history_list(current_user["agent_user_id"], int(history_id))

# 保存对话结果
@history_router.post("/saveChatResult")
def save_result(save_history: History, current_user: dict = Depends(get_current_user)):
    return history_service.save_chat_result(current_user["agent_user_id"], save_history.question, save_history.answer, save_history.parent_id)

# 删除会话历史记录
@history_router.delete("/deleteHistory/{history_id}")
def delete_history(history_id: int, current_user: dict = Depends(get_current_user)):
    return history_service.delete_history(current_user["agent_user_id"], int(history_id))
