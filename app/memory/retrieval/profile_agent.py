from app.model.my_model import MyModel
from langchain.agents import create_agent
from pydantic import BaseModel, ValidationError, field_validator
from typing import Optional
import json
import re

"""
用户画像记忆提取智能体：负责提取用户结构化数据，例如 尺码，版型，颜色，品类，材质，风格，预算，配送偏好，语言/语气
"""


class UserProfile(BaseModel):
    """用户画像 schema：只允许以下 13 个字段"""
    size_top: str | None = None
    size_bottom: str | None = None
    size_shoe: str | None = None

    fit: list[str] = []
    colors_favorite: list[str] = []
    colors_avoid: list[str] = []
    categories_favorite: list[str] = []
    categories_avoid: list[str] = []
    materials_prefer: list[str] = []
    materials_avoid: list[str] = []
    styles: list[str] = []

    budget_min: float | None = None
    budget_max: float | None = None
    budget_currency: str | None = None

    delivery_preference: str | None = None
    language: str | None = None
    tone: str | None = None

    @field_validator(
        "size_top", "size_bottom", "size_shoe",
        "delivery_preference", "language", "tone", "budget_currency",
        mode="before",
    )
    @classmethod
    def clean_text(cls, value):
        """去空白，空字符串视为没有，并限制长度"""
        if value is None:
            return None
        text = str(value).strip()
        return text[:100] if text else None

    @field_validator(
        "fit", "colors_favorite", "colors_avoid",
        "categories_favorite", "categories_avoid",
        "materials_prefer", "materials_avoid", "styles",
        mode="before",
    )
    @classmethod
    def normalize_list(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            text = value.strip()
            return [text] if text else []
        if isinstance(value, (list, tuple)):
            return [str(item).strip() for item in value if str(item).strip()]
        return []

    @field_validator("budget_min", "budget_max", mode="before")
    @classmethod
    def parse_budget(cls, value):
        if value is None or value == "":
            return None
        match = re.search(r"\d+(?:\.\d+)?", str(value))
        return float(match.group()) if match else None

class ProfileAgent:
    # 只允许落库的字段
    FIELDS = ("size_top", "size_bottom", "size_shoe", "fit", "colors_favorite", "colors_avoid", "categories_favorite", "categories_avoid", "materials_prefer", "materials_avoid", "styles", "budget_min", "budget_max", "budget_currency", "delivery_preference", "language", "tone")

    def __init__(self, profile_memory):
        # 初始化大模型：结构化抽取不需要流式，temperature=0 降低随机性
        self.model = MyModel.get_local_model().model_copy(
            update={"temperature": 0, "streaming": False, "timeout": 60, "max_retries": 0}
        )
        # 提示词
        self.prompt = self.get_prompt()
        # 初始化智能体
        self.agent = self.get_agent()
        # 初始化用户画像记忆存储对象
        self.profile_memory = profile_memory

    def get_prompt(self):
        self.prompt = """
              一: 你是一个用户画像记忆提取助手
              二：任务
                     1 只从用户当前这一句话中，提取用户本人的结构化信息
                     2 字段定义
                        size_top:上衣尺码
                        size_bottom:下装尺码
                        size_shoe:鞋码
                        fit:版型偏好，如宽松/修身
                        colors_favorite:喜欢的颜色
                        colors_avoid:不喜欢的颜色
                        categories_favorite:喜欢的品类
                        categories_avoid:不喜欢的品类
                        materials_prefer:喜欢的材质
                        materials_avoid:不喜欢/过敏的材质
                        styles:风格
                        budget_min:最低预算（数字）
                        budget_max:最高预算（数字）
                        budget_currency:币种
                        delivery_preference:配送偏好
                        language:语言
                        tone:语气
                     3 判断规则
                        - 只提取用户明确陈述的本人信息
                        - 他人的信息（例如"我朋友叫张三"）、猜测、假设、提问中的内容，一律忽略
                        - 用户没有提供的信息不要猜测，不要编造
                        - 没有可提取的信息时，返回 {}
                     4 示例
                        用户：我穿42码的鞋 返回 {"size_shoe":"42"}
                        用户：上衣一般L，喜欢宽松 返回 {"size_top":"L","fit":["宽松"]}
                        用户：不要黑色，不要聚酯纤维 返回 {"colors_avoid":["黑色"],"materials_avoid":["聚酯纤维"]}
                        用户：预算500以内 返回 {"budget_max":500,"budget_currency":"CNY"}
                        用户：我朋友穿42码 返回 {}

              三：输出
                       - 只输出 JSON
                      - 不允许输出 Markdown
                      - 不允许输出 ```json
                      - 不允许输出解释说明
                      - 不允许输出多个 JSON
                      - 不允许输出任何额外文字
                      - JSON 必须能够被 `json.loads()` 正确解析

        """
        return self.prompt

    def get_agent(self):
        self.agent = create_agent(
            model=self.model,
            system_prompt=self.prompt,
            tools=[]
        )
        return self.agent

    # 更新用户画像
    def update(self, question):
        # 提问
        try:
            rs = self.agent.invoke({"messages": [{"role": "user", "content": question}]})
        except Exception as e:
            print(f"用户画像提取调用模型出现异常:{e}")
            return {}

        # 解析并校验
        profile = self._parse_profile(rs)
        if profile is None:
            return {}

        data = profile.model_dump(exclude_none=True)
        # 白名单过滤后写入
        for key, value in data.items():
            if key not in self.FIELDS:
                continue

            if isinstance(value, list):
                if not value:
                    continue
                stored = json.dumps(value, ensure_ascii=False)
            else:
                stored = str(value).strip()
                if not stored:
                    continue

            self.profile_memory.add(key, stored)
        return data

    # 从智能体返回结果中解析出 UserProfile
    @classmethod
    def _parse_profile(cls, rs):
        answer = ""
        if isinstance(rs, dict):
            messages = rs.get("messages") or []
            if messages:
                answer = cls._content_to_text(messages[-1].content)
        elif isinstance(rs, str):
            answer = rs
        raw = cls._extract_json(answer)
        if raw is None:
            return None
        try:
            return UserProfile.model_validate(raw)
        except ValidationError as e:
            print(f"用户画像结果校验失败:{e}")
            return None

    # 把消息内容统一转成文本（兼容字符串和内容块列表）
    @staticmethod
    def _content_to_text(content):
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict):
                    parts.append(str(item.get("text", "")))
                else:
                    parts.append(str(item))
            return "".join(parts)
        return str(content or "")

    # 从模型输出中提取 JSON，兼容 Markdown 代码块和前后多余文字
    @staticmethod
    def _extract_json(text):
        if not text:
            return None
        text = text.strip()
        # 去掉 ``` 或 ```json 包裹
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end <= start:
            return None
        try:
            return json.loads(text[start:end + 1])
        except (json.JSONDecodeError, TypeError):
            return None


# 测试方法
def test():
    from app.memory.save.profile_memory import ProfileMemory

    s = ProfileMemory(1)
    # 创建画像智能体
    agent = ProfileAgent(s)
    # 正常信息
    print(agent.update("我叫王五，今年 28 岁，在清华大学做老师"))
    # 无关内容
    print(agent.update("你好，你是谁"))
    # 他人信息，不应写入
    print(agent.update("我朋友叫张三，今年30岁"))


if __name__ == "__main__":
    test()