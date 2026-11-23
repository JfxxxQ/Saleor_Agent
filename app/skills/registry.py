import re
from dataclasses import dataclass
from pathlib import Path
import yaml
from langchain.agents import create_agent
from app.agent.context import AgentContext
from app.model.my_model import MyModel
from app.tools.aftersales_tool.aftersales_tool import query_aftersales_policy
from app.tools.support_tool.product_tools import get_products
from app.tools.shopping_tool.create_checkout import create_cart
from app.tools.shopping_tool.add_checkout_lines import add_checkout_lines
from app.tools.shopping_tool.delet_checkout_line import delete_checkout_line
from app.tools.shopping_tool.get_checkout_summary import get_checkout_summary
from app.tools.shopping_tool.update_checkout_line import update_checkout_line
from app.tools.shopping_tool.get_shipping_methods import get_shipping_methods
from app.tools.shopping_tool.select_shipping_method import select_shipping_method
from app.tools.shopping_tool.place_order import place_order
from app.tools.support_tool.compare_products import compare_products
from app.tools.support_tool.generate_cypher import generate_cypher


SKILLS_DIR = Path(__file__).resolve().parent


@dataclass
class SkillSpec:
    name: str
    description: str
    instructions: str
    allowed_tools: list[str]
    path: Path

TOOL_MAP = {
    tool.name: tool
    for tool in [
        get_products,
        create_cart,
        add_checkout_lines,
        delete_checkout_line,
        get_checkout_summary,
        update_checkout_line,
        get_shipping_methods,
        select_shipping_method,
        place_order,
        compare_products,
        generate_cypher,
        query_aftersales_policy,
    ]
}


def load_skills() -> dict[str, SkillSpec]:
    skills = {}

    for skill_file in SKILLS_DIR.glob("*/SKILL.md"):
        raw = skill_file.read_text(encoding="utf-8")

        match = re.match(
            r"^---\s*\n(.*?)\n---\s*\n(.*)$",
            raw,
            re.DOTALL,
        )
        if not match:
            continue

        meta = yaml.safe_load(match.group(1)) or {}
        instructions = match.group(2).strip()

        skill = SkillSpec(
            name=meta["name"],
            description=meta["description"],
            allowed_tools=meta.get("allowed_tools", []),
            instructions=instructions,
            path=skill_file,
        )
        skills[skill.name] = skill

    return skills

SKILLS = load_skills()

BASE_PROMPT = """
你是一个电商助手。
根据当前 skill 的说明处理用户问题。
事实优先级：工具实时结果 > 图/向量检索 > 记忆。
不要编造工具没有返回的信息。
"""


def select_skill(query: str) -> SkillSpec:
    q = query.lower()
    aftersales_words = [
        "退货", "退款", "退换", "换货", "售后", "质量问题",
        "破损", "损坏", "漏液", "开线", "起球", "色差",
        "坏了", "变质", "过期", "怎么退", "能退", "可以退",
        "保修", "维修", "赔付", "补偿", "尺码不合适", "不能用",
    ]

    shopping_words = [
        "购物车", "加购", "加入购物车", "数量",
        "删除商品", "配送", "下单", "结算",
    ]

    if any(word in q for word in aftersales_words):
        return SKILLS["aftersales"]

    if any(word in q for word in shopping_words):
        return SKILLS["shopping"]

    return SKILLS["support"]


_agent_cache = {}


def build_skill_agent(skill: SkillSpec):
    if skill.name in _agent_cache:
        return _agent_cache[skill.name]

    tools = [
        TOOL_MAP[name]
        for name in skill.allowed_tools
        if name in TOOL_MAP
    ]

    prompt = BASE_PROMPT + "\n\n" + skill.instructions

    agent = create_agent(
        model=MyModel.get_line_model(),
        tools=tools,
        system_prompt=prompt,
        context_schema=AgentContext,
    )

    _agent_cache[skill.name] = agent
    return agent