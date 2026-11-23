from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.api.history_controller import history_router
from app.api.users_controller import users_router
from app.api.assistant_controller import assistant_router
from app.api.cart_controller import cart_router
from app.memory.save.long_memory import LongMemory
from app.agent.assistant_agent import ECommerceAssistant
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.assistant_agent = ECommerceAssistant()
    app.state.long_memory = LongMemory()
    print("成功加载智能电商助手")

    yield
    del app.state.assistant_agent
    del app.state.long_memory
    print("智能电商助手已清除")
app = FastAPI(
    title="Saleor Agent",
    description="基于 Saleor 的智能电商 Agent 后端",
    version="1.0.0",
    lifespan = lifespan
    )

# 跨域配置
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)

# 注册子路由
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(assistant_router, prefix="/assistant", tags=["assistant"])
app.include_router(cart_router, prefix="/cart", tags=["cart"])
app.include_router(history_router, prefix="/history", tags=["history"])


# 启动服务器
if __name__ == "__main__":
    uvicorn.run(
        app,
        host="localhost",
        port=8001,
        reload=False
    )

