# Saleor 智能购物助手（Saleor Agent）

基于 [Saleor](https://saleor.io/) 电商平台构建的对话式购物 Agent。用户可以使用自然语言完成商品搜索、商品对比、购物车管理、配送方式选择、下单以及售后退换咨询。

项目采用 Vue 3 + FastAPI + LangChain，结合 Milvus、Neo4j、ChromaDB、Redis、MySQL、PostgreSQL，实现检索增强、商品知识图谱和多层级对话记忆。

> 本项目为个人学习 / 作品项目，仓库不包含任何真实密钥。运行前请根据 `.env.example` 配置自己的环境。

## 功能特性

- **商品导购**：中文品类自动映射英文关键词，支持多关键词合并去重与商品图片卡片。
- **商品咨询**：商品属性查询、两件商品对比、基于图数据库的关联商品查询。
- **购物车**：创建 / 复用购物车、加购、修改数量、删除、查看结算摘要。
- **配送与下单**：查询 / 选择配送方式，下单前二次确认，自动校验收货地址、邮箱与配送方式。
- **售后咨询**：基于 Milvus 向量检索退货、退款、换货、破损、食品 / 数字商品等政策。
- **多轮记忆**：窗口记忆、摘要记忆、长期偏好记忆、用户画像四层记忆。
- **账户体系**：Saleor 登录注册、邮箱验证码、JWT 鉴权与角色校验。
- **流式交互**：SSE 流式输出，支持逐字渲染、停止生成、商品卡片直接加购。

## 技术栈

| 层次 | 技术 |
| --- | --- |
| 前端 | Vue 3、Vite、Pinia、Vue Router、fetch-event-source、marked、DOMPurify |
| 后端 | Python 3.12、FastAPI、Uvicorn、Pydantic v2、httpx、SSE |
| Agent | LangChain `create_agent`、ToolRuntime、OpenAI 兼容接口 |
| 检索 | Milvus 2.5、Neo4j、ChromaDB、BGE Embedding |
| 存储 | MySQL、PostgreSQL、Redis |
| 电商 | Saleor GraphQL API |
| 认证 | JWT、python-jose、邮箱验证码（SMTP） |
| 部署 | Docker Compose（Milvus Standalone） |

## 架构

```text
Vue 3 Web
   │ REST + SSE
FastAPI
   ├── Skill Router ──► shopping / support / aftersales
   ├── LangChain Agent ──► Tools
   │     ├── Saleor GraphQL：商品 / 购物车 / 配送 / 订单
   │     ├── Milvus：售后政策向量检索
   │     └── Neo4j：商品知识图谱与属性对比
   └── Memory Manager
         ├── Redis：窗口记忆、用户画像
         ├── PostgreSQL：对话摘要
         └── ChromaDB：长期偏好记忆
```

每个 Skill 由 `app/skills/*/SKILL.md` 定义处理流程、约束与工具白名单，运行时按用户意图路由并缓存对应 Agent。

## 目录结构

```text
saleor-agent/
├── app/
│   ├── agent/          # Agent 入口与运行时上下文
│   ├── api/            # FastAPI 路由
│   ├── core/           # 配置、鉴权、数据库连接
│   ├── dao/            # 数据访问层
│   ├── memory/         # 四层记忆的写入与检索
│   ├── model/          # 大模型封装
│   ├── services/       # Saleor 客户端、购物车、用户、历史记录
│   ├── skills/         # SKILL.md 与 Skill 注册表
│   └── tools/          # 导购、购物车、售后工具
├── create_data/
│   ├── Milvus/         # 商品向量索引同步
│   └── Neo4j/          # 图 Schema、商品图谱同步
├── data/               # 演示数据（Milvus 快照、售后政策表）
├── web/                # Vue 3 前端
├── docker-compose.yml  # Milvus Standalone
├── .env.example
└── requirements.txt
```

## 快速开始

### 1. 准备依赖服务

- Saleor（GraphQL API）
- MySQL、Redis、PostgreSQL、Neo4j
- Milvus：可使用本地 Milvus Lite，或执行 `docker compose up -d` 启动 Standalone
- BGE 向量模型（本地路径，配置到 `BGE_MODEL_PATH`）

### 2. 启动后端

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt

# 复制并填写环境变量
copy .env.example .env        # Windows
cp .env.example .env          # macOS / Linux

python -m app.main
```

后端默认运行在 `http://localhost:8001`，接口文档见 `http://localhost:8001/docs`。

### 3. 启动前端

```bash
cd web
npm install
npm run dev
```

前端默认运行在 `http://localhost:5173`，通过 `web/.env` 中的 `VITE_API_BASE_URL` 指定后端地址。

### 4. 初始化检索数据

```bash
# Neo4j：创建约束与索引，并同步 Saleor 商品图谱
python -m create_data.Neo4j.neo4j_schema
python -m create_data.Neo4j.neo4j_index

# Milvus：同步商品向量索引
python -m create_data.Milvus.milvus_index
```

售后政策集合的演示数据已包含在 `data/milvus_products.db` 中，原始政策表见 `data/saleor_product_return_policies_*.xlsx`。

## 环境变量

完整配置项见 [`.env.example`](.env.example)，主要包括：

- `SALEOR_*`：Saleor GraphQL 地址、Token、Channel
- `LLM_*` / `LOCAL_URL` / `DASHSCOPE_API_KEY`：主模型与本地模型配置
- `JWT_*`：登录令牌配置
- `MYSQL_*` / `REDIS_*` / `PG_URL` / `NEO4J_*` / `MILVUS_*`：数据存储连接
- `BGE_*` / `CHROM_DB_*`：向量模型与长期记忆配置
- `SMTP_*`：注册验证码邮件发送

## 说明与限制

- 下单流程预留了 Saleor 支付扩展点。若未安装支付 App，`checkoutComplete` 会返回 `CHECKOUT_NOT_FULLY_PAID`，需要先完成支付后才能生成订单。
- `data/milvus_products.db` 是演示数据快照，可通过同步脚本重建商品集合。
- 记忆只作为回答参考，商品价格、库存、订单状态与售后政策以工具实时查询结果为准。
- 请勿将 `.env` 或任何真实密钥提交到仓库。
