import os
from dotenv import load_dotenv

#读取配置文件
load_dotenv()

"""
提示词构建器：把四层记忆（窗口、摘要、长期、画像）装配成一段文本，
作为 system 消息交给聊天模型使用。
"""
class PromptBuilder:

    def __init__(self, window_memory, summary_memory, long_memory, profile_memory, agent_user_id, history_id, question):
        self.window_memory = window_memory
        self.summary_memory = summary_memory
        self.long_memory = long_memory
        self.profile_memory = profile_memory
        self.agent_user_id = agent_user_id
        self.history_id = history_id
        self.question = question
        #长期记忆的向量距离阈值，超过该值视为不相关，可通过环境变量调整
        self.max_distance = float(os.getenv("LONG_MEMORY_MAX_DISTANCE"))

#构建提示词
    def builder(self):
        #记忆使用说明：告诉模型这些数据怎么用，以及冲突时的优先级
        sections = ["以下是与用户相关的记忆，仅供回答时参考。这些记忆可能过时，也可能来自之前对话中的错误结论。商品是否存在、价格、库存、规格，以工具实时查询结果为准；记忆与工具结果冲突时，以工具结果为准。"]

        #窗口记忆：跳过空内容，避免拼出空行
        window_lines = []
        for item in self.window_memory.load():
            content = item.get("content", "")
            if content:
                role = item.get("role", "")
                window_lines.append(f"短期记忆：{role}:{content}")
        if window_lines:
            sections.append("\n".join(window_lines))

        #摘要记忆：为空时不输出空标签
        summary = self.summary_memory.load_memory(self.history_id)
        if summary:
            sections.append(f"摘要记忆：{summary}")

        #长期记忆：按向量距离过滤掉明显不相关的检索结果
        long_memories = self.long_memory.load_memory(
            self.agent_user_id, self.question, max_distance=self.max_distance
        )
        if long_memories:
            sections.append("长期记忆：\n" + "\n".join(long_memories))

        #用户画像：为空时不输出空标签
        profile = self.profile_memory.load()
        if profile and profile.strip():
            sections.append("用户画像：\n" + profile.strip())

        return "\n".join(sections) + "\n"