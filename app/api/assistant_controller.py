from fastapi import Depends, APIRouter, Request
from starlette.responses import StreamingResponse
from app.core.security import get_current_user
import json
import logging


assistant_router = APIRouter()
logger = logging.getLogger(__name__)


@assistant_router.post("/chat")
async def chat(
    question: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    async def generator():
        try:
            async for event in request.app.state.assistant_agent.run(
                question,
                current_user,
            ):
                # event 可能是：
                # {"content": "文本"}
                # {"type": "products", "items": [...]}
                # {"error": "..."}
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

            yield f"data: {json.dumps({'content': '[DONE]'}, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.exception("聊天流式异常")
            error_msg = str(e)
            yield f"data: {json.dumps({'error': error_msg}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'content': '[DONE]'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        content=generator(),
        media_type="text/event-stream",
    )