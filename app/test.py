from create_data.Milvus.milvus import get_client, ensure_collection
from app.core.load_milvus_conn import LoadMilvusConn

# client = get_client()
# ensure_collection(client)
#
# vec = LoadMilvusConn.embed_query("果汁")
# result = client.search(
#     "products",
#     data=[vec],
#     anns_field="embedding",
#     search_params={"metric_type": "COSINE", "params": {}},
#     limit=3,
#     filter="is_active == true",
#     output_fields=["name", "category"],
# )
# print(result)

# from neo4j import GraphDatabase
#
# driver = GraphDatabase.driver(
#     "neo4j://127.0.0.1:7687",
#     auth=("neo4j", "<NEO4J_PASSWORD>"),
# )
# driver.verify_connectivity()
# print("Neo4j connected")
# driver.close()

from app.skills.registry import SKILLS, select_skill

print("skills:", list(SKILLS.keys()))
print("果汁坏了怎么退 ->", select_skill("果汁坏了怎么退").name)
print("帮我找T恤 ->", select_skill("帮我找T恤").name)
print("加购物车 ->", select_skill("把 Monospace Tee 加入购物车").name)


# import asyncio
# from app.agent.context import AgentContext
# from app.skills.registry import SKILLS, build_skill_agent
#
# ctx = AgentContext(
#     agent_user_id=31,
#     saleor_user_id="VXNlcjo0Ng==",
#     role="user",
# )
#
# async def main():
#     for name, question in [
#         ("support", "有哪些果汁"),
#         ("aftersales", "果汁漏液了怎么办"),
#     ]:
#         agent = build_skill_agent(SKILLS[name])
#         result = await agent.ainvoke(
#             {"messages": [{"role": "user", "content": question}]},
#             context=ctx,
#         )
#         print(name, "=>", result["messages"][-1].content)
#
# asyncio.run(main())
