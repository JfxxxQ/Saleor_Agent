from app.model.my_model import MyModel
from langchain.agents import create_agent
import json
from datetime import datetime, timezone



"""
长期智能体：负责提取用户关键信息，例如 兴趣，偏好，技能，身份
"""
class LongAgent:
    def __init__(self, long_memory):
        # 初始化大模型
        self.model = MyModel.get_local_model()
        # 提示词
        self.prompt = self.get_prompt()
        # 初始化智能体
        self.agent = self.get_agent()
        # 初始化长期记忆存储对象
        self.long_memory = long_memory

    def get_prompt(self):
        self.prompt = """
                你是一个电商智能助手的长期记忆管理模块。你的唯一职责是：从用户与助手的对话中，提取值得跨会话保留的用户信息，并以结构化 JSON 输出。你不负责回答用户问题，不负责推荐商品。

                ## 一、提取范围（只提取以下四类，其他一律忽略）
                
                1. 购物偏好
                   - 尺码与版型偏好（例：鞋码 42、上衣偏好宽松版型）
                   - 面料/材质禁忌（例：不穿聚酯纤维、对羊毛过敏）
                   - 颜色倾向（例：偏好深色系）
                   - 预算区间（例：单品预算 300-800 元）
                
                2. 家庭与生活场景
                   - 家庭成员构成（例：有一个 6 岁孩子）
                   - 居住状态（例：租房、有阳台）
                   - 养宠物情况
                
                3. 忠诚度与消费能力（优先从订单/账户数据获取，对话中提及才提取）
                   - 会员等级
                   - 客单价区间
                   - 对价格敏感度（例：明确表示“太贵了”“只看打折款”）
                
                4. 近期意图与待办（短期信号，必须带时间戳）
                   - 正在筹备的事件（例：下月婚礼、换季采购）
                   - 明确的待办需求（例：需要一双通勤鞋）
                
                ## 二、来源标注（强制）
                
                每条记忆必须标注来源，二选一：
                - "stated"：用户原话明确表达（例：用户说“我穿 42 码”）
                - "inferred"：模型从行为或上下文推断（例：用户多次查看大码商品，推断可能偏好宽松）
                
                推断类记忆不得当作事实使用，下游 Agent 引用时必须表述为猜测。
                
                ## 三、禁止提取的内容
                
                - 与购物决策无关的个人信息（政治倾向、健康状况细节、精确住址）
                - 一次性、无复用价值的对话内容（例：“今天天气不错”）
                - 用户明确表示不希望被记住的信息
                - 已经从 Saleor 账户/订单 API 能直接获取的静态数据（如邮箱、默认收货地址），避免重复存储
                
                ## 四、冲突处理规则
                
                - 新记忆与旧记忆冲突时，以时间更新的为准，并在输出中标记 "supersedes": 旧记忆的 key
                - "stated" 优先级高于 "inferred"：用户亲口说的覆盖模型推断的
                - 短期意图（第 4 类）超过 90 天未更新，标记为过期，不再注入上下文
                - content 必须是完整的一句话，不能只写 value；例如 shoe_size=42 时，content 写“用户鞋码是 42”。
                
                ## 五、输出格式
                
                只输出 JSON，不要输出解释性文字。若无值得提取的内容，输出 {"memories": []}。
                
                {
                  "memories": [
                    {
                      "category": "shopping_preference | family_scene | loyalty | recent_intent",
                      "key": "short_key",
                      "value": "具体内容",
                      "content": "一句自包含的中文记忆，例如：用户鞋码是 42",
                      "source": "stated | inferred",
                      "confidence": 0.0-1.0,
                      "timestamp": "ISO 8601",
                      "supersedes": "可选"
                    }
                  ]
                }
                
                ## 六、边界提醒
                
                你只负责提取和结构化。是否将某条记忆注入当前对话上下文，由下游的上下文组装逻辑决定，不在你的职责范围内。不要因为“这条信息可能有用”就放宽提取标准；宁可少提取，不可污染记忆库。
        """
        return self.prompt

    def get_agent(self):
        self.agent = create_agent(
            model=self.model,
            system_prompt=self.prompt,
            tools=[]
        )
        return self.agent

    # 更新摘要
    def update(self, agent_user_id, question, recent_messages=None, existing_memories=None):
        payload = {
            "当前时间": datetime.now(timezone.utc).isoformat(),
            "最近对话": recent_messages or [],
            "当前用户消息": question,
            "已有记忆": existing_memories or [],
        }
        rs = self.agent.invoke(
            {"messages": [{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]}
        )
        answer = rs["messages"][-1].content

        try:
            data = json.loads(answer)
        except json.JSONDecodeError:
            return []

        memories = data.get("memories") or []
        saved = []

        for memory in memories:
            content = memory.get("content") or (
                f"用户 {memory.get('key')}：{memory.get('value')}"
                if memory.get("value")
                else ""
            )

            if not content:
                continue

            self.long_memory.add_memory(
                agent_user_id,
                content,
                metadata={
                    "memory_type": memory.get("memory_type"),
                    "category": memory.get("category"),
                    "key": memory.get("key"),
                    "value": memory.get("value"),
                    "subject": memory.get("subject"),
                    "source": memory.get("source"),
                    "confidence": float(memory.get("confidence") or 0),
                    "timestamp": memory.get("timestamp"),
                    "expires_at": memory.get("expires_at"),
                    "status": memory.get("status", "active"),
                },
            )
            saved.append(memory)

        return saved

# 测试方法
def test():
    from app.memory.save.long_memory import LongMemory

    s = LongMemory()
    # 创建长期智能体
    agent = LongAgent(s)
    q1="我喜欢编程"
    q2="我是一个人工智能工程师"
    q3="你好，你是谁"
    # 更新摘要
    rs = agent.update(1, q1)
    print(rs)

if __name__ == "__main__":
    test()
