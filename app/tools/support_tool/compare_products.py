from app.core.load_neo4j_conn import LoadNeo4jConn
from langchain.tools import tool
from pydantic import BaseModel, Field


class CompareProductsInput(BaseModel):
    product_id_a: str = Field(...)
    product_id_b: str = Field(...)


@tool(args_schema=CompareProductsInput)
def compare_products(product_id_a: str, product_id_b: str):
    """比较两个产品的属性。"""
    cypher = """
    MATCH (a:Product {id: $a_id}), (b:Product {id: $b_id})
    OPTIONAL MATCH (a)-[:HAS_ATTRIBUTE]->(aa:AttributeValue)
    OPTIONAL MATCH (b)-[:HAS_ATTRIBUTE]->(ba:AttributeValue)
    RETURN a.id AS a_id,
           a.name AS a_name,
           b.id AS b_id,
           b.name AS b_name,
           collect(DISTINCT {key: aa.key, value: aa.value}) AS a_attributes,
           collect(DISTINCT {key: ba.key, value: ba.value}) AS b_attributes
    LIMIT $limit
    """
    params = {
        "a_id": product_id_a,
        "b_id": product_id_b,
        "limit": 10,
    }
    driver = LoadNeo4jConn.get_driver()
    with driver.session(database=LoadNeo4jConn.database()) as session:
        return session.execute_read(
            lambda tx: tx.run(cypher, params).data()
        )


if __name__ == "__main__":
    print(compare_products.invoke({"product_id_a": "UHJvZHVjdDoxMzQ=", "product_id_b": "UHJvZHVjdDoxMzc="}))
