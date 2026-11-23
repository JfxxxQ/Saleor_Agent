from langchain.agents import create_agent
from langchain_core.messages import AIMessageChunk
from app.memory.save.conversation_manager import ConversationManager
from app.memory.memory_manager import MemoryManager
from app.agent.context import AgentContext
from app.model.my_model import MyModel
import asyncio
import logging
from app.skills.registry import build_skill_agent, select_skill



logger = logging.getLogger(__name__)


"""
电商购物助手
"""
class ECommerceAssistant:
    def __init__(self):
        self.local_model = MyModel.get_local_model()
        self.model = MyModel.get_line_model()
        self.tool = self.get_tool()
        self.prompt = self.get_prompt()
        self.agent = self.get_agent()
        # 保存后台记忆更新任务，避免任务对象被垃圾回收
        self._memory_tasks = set()

    def get_prompt(self):
        self.prompt = """
            一、角色：你是电商助手。
            二、事实优先级：工具实时结果 > 图/向量检索 > 记忆。
            三、根据系统选中的 skill 处理问题，不要跨 skill 编造业务规则。
            四、不要编造商品、价格、库存、订单或售后政策。
        """
        return self.prompt

    def get_tool(self):
        self.tool = []
        return self.tool

    def get_agent(self):
        self.agent = create_agent(
            model = self.model,
            tools = self.tool,
            system_prompt = self.prompt,
            context_schema=AgentContext,
        )
        return self.agent

    async def run(self, query: str, current_user: dict):
        agent_user_id = current_user["agent_user_id"]
        saleor_user_id = current_user["saleor_user_id"]

        try:
            # 添加四层记忆
            c = ConversationManager(agent_user_id, agent_user_id, query)
            m = MemoryManager(c)
            # 添加窗口记忆用户问题
            c.add_window("user", query)
            # 构建记忆的提示词
            memory_prompt = c.add_prompt()
            # 构建一个系统角色消息
            sys_msg = {"role": "system", "content": memory_prompt}
            msg = {
                "messages": [
                    sys_msg,
                    {"role": "user", "content": query},
                ]
            }
            config = {"configurable": {"thread_id": agent_user_id}}
            context = AgentContext(
                agent_user_id=agent_user_id,
                saleor_user_id=saleor_user_id,
                role=current_user["role"]
            )
            answer_parts = []
            skill = select_skill(query)
            agent = build_skill_agent(skill)
            async for mode, chunk in agent.astream(
                    msg,
                    config=config,
                    context=context,
                    stream_mode=["messages", "custom"],
            ):
                # 模型输出的文本
                if mode == "messages":
                    message_chunk, _metadata = chunk

                    if isinstance(message_chunk, AIMessageChunk):
                        for text in self._extract_text(message_chunk.content):
                            answer_parts.append(text)
                            yield {"content": text}
                # 工具通过 runtime.stream_writer 发出的结构化事件
                elif mode == "custom":
                    if isinstance(chunk, dict) and chunk.get("type") == "products":
                        yield chunk
            answer = "".join(answer_parts)
            c.add_window("assistant", answer)
            self._schedule_memory_update(m, query)
        except Exception:
            logger.exception("异步聊天异常")
            yield {"error": "聊天服务暂时不可用"}

    # 真正执行记忆更新（在线程池中运行，避免阻塞事件循环）
    def _update_memory(self, manager, question):
        try:
            manager.update(question)
        except Exception as e:
            print(f"更新记忆出现异常:{e}")

    # 调度后台任务更新记忆
    def _schedule_memory_update(self, manager, question):
        task = asyncio.create_task(asyncio.to_thread(self._update_memory, manager, question))
        self._memory_tasks.add(task)
        task.add_done_callback(self._memory_tasks.discard)

    @staticmethod
    def _extract_text(content):
        if isinstance(content, str):
            if content:
                yield content
        elif isinstance(content, list):
            # 兼容多模态/Anthropic 风格的 content blocks
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text = block.get("text", "")
                    if text:
                        yield text

async def test():
    assistant = ECommerceAssistant()
    current_user = {
        "agent_user_id": 31,
        "saleor_user_id": "VXNlcjo0Ng==",
        "role": "user",
    }

    async for event in assistant.run("果汁漏液了怎么办", current_user):
        if event.get("content"):
            print(event["content"], end="", flush=True)
        elif event.get("type") == "products":
            print(f"\n[商品卡片: {len(event.get('items', []))} 件]")
        elif event.get("error"):
            print(f"\n[错误] {event['error']}")

if __name__ == "__main__":
    asyncio.run(test())
