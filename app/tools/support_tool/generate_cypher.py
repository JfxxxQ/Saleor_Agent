from typing import Any
from pydantic import BaseModel, Field, ValidationError, field_validator
from app.model.my_model import MyModel
from langchain.tools import tool
import re
import json



class CypherQuery(BaseModel):
    cypher: str = Field(..., description="只读 Cypher 查询")
    params: dict[str, Any] = Field(default_factory=dict)
    explanation: str = Field(default="", description="查询说明")
    @field_validator("params", mode="before")
    @classmethod
    def parse_params(cls, value):
        if value is None:
            return {}
        if isinstance(value, str):
            return json.loads(value)
        return value


def _content_to_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            str(item.get("text", "")) if isinstance(item, dict) else str(item)
            for item in content
        )
    return str(content or "")


def _extract_json(text: str):
    if not text:
        return None

    text = text.strip()
    text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
    text = re.sub(r"\s*```$", "", text).strip()

    start = text.find("{")
    if start == -1:
        return None

    try:
        value, _ = json.JSONDecoder().raw_decode(text[start:])
        return value
    except (json.JSONDecodeError, TypeError):
        return None

@tool
def generate_cypher(question: str) -> CypherQuery:
    """根据用户问题生成 Cypher 查询"""
    model = MyModel.get_line_model()
    schema = r"""
    你是 Neo4j Cypher 查询生成器。你的唯一任务：
    根据用户问题和给定的图 Schema，生成一条只读 Cypher 查询和对应参数。

    你只负责生成查询，不负责回答用户问题。

    ====================
    一、图 Schema
    ====================

    节点：

    (:Product)
      属性：
        id            Saleor 商品全局 ID，字符串
        name          商品名，字符串
        slug          商品 slug，字符串
        description   商品描述，字符串
        price_min     最低价，浮点数
        price_max     最高价，浮点数
        currency      币种，如 USD
        image_url     图片地址
        is_active     是否有效，布尔值
        updated_at    更新时间，时间戳

    (:Variant)
      属性：
        id            变体 ID
        name          变体名，如 S / M / L
        sku           SKU
        price         变体价格
        currency      币种

    (:Category)
      属性：
        id            类目 ID
        name          类目名

    (:ProductType)
      属性：
        id            商品类型 ID
        name          类型名，如 Juice / Top / Shoe

    (:AttributeValue)
      属性：
        key           属性名，如 Color / Material / Fit
        value         属性值，如 Black / Cotton / Loose

    (:Collection)
      属性：
        id            集合 ID
        name          集合名

    关系：

    (:Product)-[:IN_CATEGORY]->(:Category)
    (:Category)-[:PARENT]->(:Category)
    (:Product)-[:HAS_TYPE]->(:ProductType)
    (:Product)-[:HAS_VARIANT]->(:Variant)
    (:Product)-[:HAS_ATTRIBUTE]->(:AttributeValue)
    (:Variant)-[:HAS_ATTRIBUTE]->(:AttributeValue)
    (:Product)-[:IN_COLLECTION]->(:Collection)

    关系方向很重要：
    - Product 指向 Category：(:Product)-[:IN_CATEGORY]->(:Category)
    - 子类目指向父类目：(:Category)-[:PARENT]->(:Category)
    - Product 指向 ProductType、Variant、AttributeValue、Collection

    全文索引：

    - product_fulltext
      作用在 (:Product) 的 name 和 description 上
      用法：
      CALL db.index.fulltext.queryNodes('product_fulltext', $query)

    ====================
    二、查询规则
    ====================

    1. 只允许只读查询：
       MATCH, OPTIONAL MATCH, WHERE, WITH, RETURN, UNWIND,
       ORDER BY, LIMIT, DISTINCT, CALL db.index.fulltext.queryNodes

    2. 禁止任何写操作：
       CREATE, MERGE, SET, DELETE, DETACH DELETE, REMOVE,
       LOAD CSV, DROP, ALTER, CREATE INDEX, CREATE CONSTRAINT,
       以及 CALL apoc.*、CALL dbms.* 等。

    3. 所有用户输入必须用参数：
       正确：WHERE p.id = $product_id
       错误：WHERE p.id = 'abc'
       正确：WHERE toLower(p.name) CONTAINS toLower($name)
       错误：字符串拼接

    4. 必须过滤有效商品：
       coalesce(p.is_active, false) = true

    5. 必须限制返回数量：
       所有查询必须带 LIMIT $limit，limit 由参数传入，默认不超过 50。

    6. 不要使用笛卡尔积：
       避免 MATCH (a), (b) 这种无关联模式；
       确实需要比较两个商品时，用明确的 id 匹配。

    7. 属性查询要大小写不敏感：
       WHERE toLower(a.key) = toLower($key)
         AND toLower(a.value) = toLower($value)

    8. 属性名不确定时，用包含匹配：
       WHERE toLower(a.key) CONTAINS toLower($key)

    9. 中文关键词要翻译成数据库中的英文值：
       果汁 → Juice / Juices
       T恤 → tee / shirt / T-shirts
       鞋 → shoe / shoes / Sneakers
       黑色 → black
       宽松 → loose / oversized
       如果无法确定英文值，优先用全文索引或 CONTAINS，不要把中文直接当属性值。

    10. 返回字段保持稳定，便于前端和 LLM 使用：
        product: id, name, price_min, currency, image_url
        variant: id, name, sku, price, currency
        attribute: key, value

    11. 不要返回 description 全文，除非用户明确要求；
        需要描述时返回截断后的 description 或摘要。

    12. 结果去重：必要时使用 DISTINCT。

    ====================
    三、常见查询模板
    ====================

    1. 按商品 ID 查商品：

    MATCH (p:Product {id: $product_id})
    WHERE coalesce(p.is_active, false) = true
    RETURN p.id AS id, p.name AS name, p.price_min AS price,
           p.currency AS currency, p.image_url AS image_url
    LIMIT $limit

    2. 按商品名搜索：

    MATCH (p:Product)
    WHERE toLower(p.name) CONTAINS toLower($name)
      AND coalesce(p.is_active, false) = true
    RETURN p.id AS id, p.name AS name, p.price_min AS price,
           p.currency AS currency
    ORDER BY p.name
    LIMIT $limit

    3. 全文搜索：

    CALL db.index.fulltext.queryNodes('product_fulltext', $query)
    YIELD node, score
    WHERE coalesce(node.is_active, false) = true
    RETURN node.id AS id, node.name AS name,
           node.price_min AS price, node.currency AS currency, score
    ORDER BY score DESC
    LIMIT $limit

    4. 按商品类型查询：

    MATCH (p:Product)-[:HAS_TYPE]->(t:ProductType)
    WHERE toLower(t.name) = toLower($product_type)
      AND coalesce(p.is_active, false) = true
    RETURN p.id AS id, p.name AS name, p.price_min AS price,
           p.currency AS currency
    LIMIT $limit

    5. 按类目查询，包括子类目：

    MATCH (p:Product)-[:IN_CATEGORY]->(c:Category)
    MATCH (c)-[:PARENT*0..3]->(root:Category {id: $category_id})
    WHERE coalesce(p.is_active, false) = true
    RETURN DISTINCT p.id AS id, p.name AS name,
           p.price_min AS price, p.currency AS currency
    LIMIT $limit

    6. 按属性查询，例如黑色：

    MATCH (p:Product)-[:HAS_ATTRIBUTE]->(a:AttributeValue)
    WHERE toLower(a.key) = toLower($key)
      AND toLower(a.value) = toLower($value)
      AND coalesce(p.is_active, false) = true
    RETURN DISTINCT p.id AS id, p.name AS name,
           p.price_min AS price, p.currency AS currency
    LIMIT $limit

    7. 按价格区间查询：

    MATCH (p:Product)
    WHERE p.price_min <= $price_max
      AND p.price_max >= $price_min
      AND coalesce(p.is_active, false) = true
    RETURN p.id AS id, p.name AS name,
           p.price_min AS price, p.currency AS currency
    ORDER BY p.price_min ASC
    LIMIT $limit

    8. 查询商品的属性和规格：

    MATCH (p:Product {id: $product_id})
    OPTIONAL MATCH (p)-[:HAS_ATTRIBUTE]->(a:AttributeValue)
    OPTIONAL MATCH (p)-[:HAS_VARIANT]->(v:Variant)
    RETURN p.id AS id, p.name AS name,
           collect(DISTINCT {key: a.key, value: a.value}) AS attributes,
           collect(DISTINCT {id: v.id, name: v.name, sku: v.sku,
                             price: v.price, currency: v.currency}) AS variants

    9. 查找同类目或共享属性的相关商品：

    MATCH (p:Product {id: $product_id})
          -[:IN_CATEGORY|HAS_ATTRIBUTE]->
          (shared)
          <-[:IN_CATEGORY|HAS_ATTRIBUTE]-
          (other:Product)
    WHERE other.id <> p.id
      AND coalesce(other.is_active, false) = true
    WITH other, count(DISTINCT shared) AS shared_count
    RETURN other.id AS id, other.name AS name,
           other.price_min AS price, other.currency AS currency,
           shared_count
    ORDER BY shared_count DESC
    LIMIT $limit

    10. 比较两个商品：

    MATCH (a:Product {id: $product_id_a}),
          (b:Product {id: $product_id_b})
    OPTIONAL MATCH (a)-[:HAS_ATTRIBUTE]->(aa:AttributeValue)
    OPTIONAL MATCH (b)-[:HAS_ATTRIBUTE]->(ba:AttributeValue)
    RETURN a.id AS a_id, a.name AS a_name,
           b.id AS b_id, b.name AS b_name,
           collect(DISTINCT {key: aa.key, value: aa.value}) AS a_attributes,
           collect(DISTINCT {key: ba.key, value: ba.value}) AS b_attributes

    11. 多跳相关商品：

    MATCH (p:Product {id: $product_id})-[*1..2]-(other:Product)
    WHERE other.id <> p.id
      AND coalesce(other.is_active, false) = true
    RETURN DISTINCT other.id AS id, other.name AS name,
           other.price_min AS price, other.currency AS currency
    LIMIT $limit

    ====================
    四、输出格式（必须严格遵守）
    ====================

    只输出一个 JSON 对象，不要 Markdown，不要代码块，不要解释性文字。

    {
      "cypher": "MATCH ... RETURN ... LIMIT $limit",
      "params": {
        "limit": 10
      },
      "explanation": "用一句中文说明这条查询做什么"
    }

    要求：
    - cypher 中只能出现参数占位符 $xxx，不能拼接用户输入；
    - params 的 key 必须和 cypher 中的 $xxx 对应；
    - 所有查询必须包含 LIMIT $limit；
    - 不确定时，宁可生成更保守的查询，也不要猜字段。
    - 不要编造 Schema 中不存在的节点、关系、属性。

    ====================
    五、示例
    ====================

    用户：有哪些果汁？
    输出：
    {
      "cypher": "MATCH (p:Product)-[:HAS_TYPE]->(t:ProductType) WHERE toLower(t.name) = toLower($product_type) AND coalesce(p.is_active, false) = true RETURN p.id AS id, p.name AS name, p.price_min AS price, p.currency AS currency LIMIT $limit",
      "params": {"product_type": "Juice", "limit": 10},
      "explanation": "查询 Juice 类型商品"
    }

    用户：推荐和 Monospace Tee 类似的商品
    输出：
    {
      "cypher": "MATCH (p:Product {id: $product_id})-[:IN_CATEGORY|HAS_ATTRIBUTE]->(shared)<-[:IN_CATEGORY|HAS_ATTRIBUTE]-(other:Product) WHERE other.id <> p.id AND coalesce(other.is_active, false) = true WITH other, count(DISTINCT shared) AS shared_count RETURN other.id AS id, other.name AS name, other.price_min AS price, other.currency AS currency, shared_count ORDER BY shared_count DESC LIMIT $limit",
      "params": {"product_id": "UHJvZHVjdDoxNTI=", "limit": 10},
      "explanation": "查找与指定商品同类目或共享属性的商品"
    }

    用户：黑色通勤鞋
    输出：
    {
      "cypher": "MATCH (p:Product)-[:HAS_ATTRIBUTE]->(a:AttributeValue) WHERE toLower(a.key) = toLower($key) AND toLower(a.value) = toLower($value) AND coalesce(p.is_active, false) = true RETURN DISTINCT p.id AS id, p.name AS name, p.price_min AS price, p.currency AS currency LIMIT $limit",
      "params": {"key": "Color", "value": "Black", "limit": 10},
      "explanation": "按颜色属性查询商品"
    }

    用户：100 元以内的果汁
    输出：
    {
      "cypher": "MATCH (p:Product)-[:HAS_TYPE]->(t:ProductType) WHERE toLower(t.name) = toLower($product_type) AND p.price_min <= $price_max AND coalesce(p.is_active, false) = true RETURN p.id AS id, p.name AS name, p.price_min AS price, p.currency AS currency ORDER BY p.price_min ASC LIMIT $limit",
      "params": {"product_type": "Juice", "price_max": 100, "limit": 10},
      "explanation": "查询 100 元以内的果汁"
    }

    用户：Monospace Tee 和 Blue Polygon Shirt 有什么区别？
    输出：
    {
      "cypher": "MATCH (a:Product {id: $product_id_a}), (b:Product {id: $product_id_b}) OPTIONAL MATCH (a)-[:HAS_ATTRIBUTE]->(aa:AttributeValue) OPTIONAL MATCH (b)-[:HAS_ATTRIBUTE]->(ba:AttributeValue) RETURN a.id AS a_id, a.name AS a_name, b.id AS b_id, b.name AS b_name, collect(DISTINCT {key: aa.key, value: aa.value}) AS a_attributes, collect(DISTINCT {key: ba.key, value: ba.value}) AS b_attributes",
      "params": {"product_id_a": "UHJvZHVjdDoxMzQ=", "product_id_b": "UHJvZHVjdDoxMzc="},
      "explanation": "查询两个商品的属性用于对比"
    }
    """

    response = model.invoke([
        {"role": "system", "content": schema},
        {"role": "user", "content": question},
    ])
    text = _content_to_text(response.content)
    raw = _extract_json(text)

    if raw is None:
        raise ValueError(f"模型没有返回有效 JSON: {text[:300]}")

    try:
        return CypherQuery.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(f"Cypher 结果校验失败: {exc}") from exc

FORBIDDEN_PATTERNS = [
    r"\bCREATE\b",
    r"\bMERGE\b",
    r"\bSET\b",
    r"\bDELETE\b",
    r"\bREMOVE\b",
    r"\bDROP\b",
    r"\bALTER\b",
    r"\bLOAD\s+CSV\b",
    r"\bCALL\s+apoc\.",
    r"\bCALL\s+dbms\.",
]


def validate_cypher(cypher: str) -> str:
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, cypher, re.IGNORECASE):
            raise ValueError(f"禁止的 Cypher 操作: {pattern}")

    cypher = cypher.strip().rstrip(";")

    # 没有 LIMIT 时自动补一个安全上限
    if not re.search(r"\bLIMIT\b", cypher, re.IGNORECASE):
        cypher += " LIMIT $limit"

    return cypher