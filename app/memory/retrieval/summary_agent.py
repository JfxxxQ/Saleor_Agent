from app.model.my_model import MyModel
from langchain.agents import create_agent
"""
摘要智能体，负责提取用户摘要记忆
"""
class SummaryAgent:
    def __init__(self, summary_memory):
        #初始化大模型
        self.model = MyModel.get_local_model()
        #提示词
        self.prompt = self.get_prompt()
        #初始化智能体
        self.agent = self.get_agent()
        #初始化只要记忆存储对象
        self.summary_memory = summary_memory


    def get_prompt(self):
        self.prompt = """
             你是一个电商对话摘要助手。
                你的任务：把【历史摘要】和【最近聊天记录】合并成一段新的摘要。
                
                要求：
                1. 只输出新的摘要，不要解释、不要 Markdown、不要“摘要：”前缀。
                2. 使用第三人称，中文，控制在 200 字以内。
                3. 只保留对后续购物有用的信息：
                   - 用户的需求、偏好、尺码、预算、配送要求；
                   - 已确认的商品、规格、数量、购物车或订单关键状态；
                   - 未完成的任务、待确认事项、重要决定。
                4. 去掉寒暄、重复内容、助手泛泛的解释、工具调用细节。
                5. 合并历史摘要：仍然有效的信息保留，新信息覆盖旧信息，不要重复。
                6. 不编造、不推测；只总结输入中出现的内容。
                7. 区分用户陈述和助手建议，例如“用户表示…”“助手建议…”。
                8. 不写详细地址、电话、邮箱、支付信息；必要时写“用户已提供收货信息”。
                9. 最近聊天记录为空时，原样返回历史摘要；历史摘要也为空时，返回 0。
                10. 最近聊天没有产生新的重要信息时，返回 0。
                11. 只输出一段摘要，不要输出多条。
                12. 不要记录助手关于商品库存、商品是否存在、价格的未经验证结论，
                    这些信息只能以工具查询结果为依据，
                    只记录用户明确表达的需求、偏好，以及已经由工具确认的选择。

                
                示例 1：
                历史摘要：（无）
                最近聊天记录：
                用户：你好
                助手：你好，我是购物助手
                输出：0
                
                示例 2：
                历史摘要：（无）
                最近聊天记录：
                用户：帮我找T恤
                助手：我找到了 Monospace Tee、Blue Polygon Shirt 等
                用户：要 Monospace Tee 的 M 码，加两件
                输出：用户想购买 T 恤，已选择 Monospace Tee M 码 2 件，等待确认加购或下单。
                
                示例 3：
                历史摘要：用户正在为婚礼挑选衬衫，预算 500 元以内。
                最近聊天记录：
                用户：就选那件白色的吧
                助手：好的，已记录
                输出：用户正在为婚礼挑选衬衫，预算 500 元以内，已确定选择白色款。
        """
        return self.prompt

    def get_agent(self):
        self.agent = create_agent(
            model = self.model,
            system_prompt = self.prompt,
            tools = []
        )
        return self.agent

    #更新摘要
    def update(self, history_id, messages):
        #获取历史摘要
        history = self.summary_memory.load_memory(history_id) or ""
        if not messages:
            return history or "0"
        #最新消息
        lines = []
        #提取窗口记忆的信息
        for x in messages:
            role = x.get("role", "user")
            content = x.get("content", "")
            if content is None:
                continue
            role_name = "用户" if role in ("user", "human") else "助手"
            lines.append(f"{role_name}：{content}")

        new_msg = "\n".join(lines)
        if not new_msg.strip():
            return history or "0"
        #拼接问题
        question = (
        f"历史摘要：{history or '（无）'}\n"
        f"最近聊天记录：\n{new_msg}"
    )
        try:
            rs = self.agent.invoke(
                {"messages": [{"role": "user", "content": question}]}
            )
            answer = str(rs["messages"][-1].content).strip()
        except Exception as e:
            print(f"摘要生成失败: {e}")
            return history or "0"

        if answer in ("", "0", "无"):
            return "0"

        if answer.startswith("摘要："):
            answer = answer[len("摘要："):].strip()

        answer = answer[:300]

        try:
            self.summary_memory.add_memory(history_id, answer)
        except Exception as e:
            print(f"摘要保存失败: {e}")

        return answer
#测试方法
def test():
    from app.memory.save.summary_memory import SummaryMemory
    from app.memory.save.window_memory import WindowMemory
    s = SummaryMemory()
    w = WindowMemory(1)
    #创建摘要智能体
    agent = SummaryAgent(s)
    #更新摘要
    rs = agent.update(1, w.load())
    print(rs)

if __name__ == "__main__":
    test()
