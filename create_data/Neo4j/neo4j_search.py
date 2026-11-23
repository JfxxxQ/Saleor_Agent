from app.core.load_neo4j_conn import LoadNeo4jConn


def _session():
    driver = LoadNeo4jConn.get_driver()
    return driver.session(database=LoadNeo4jConn.database())


def search_products_fulltext(query: str, limit: int = 10) -> list[dict]:
    with _session() as session:
        result = session.run(
            """
            CALL db.index.fulltext.queryNodes('product_fulltext', $query)
            YIELD node, score
            WHERE node.is_active = true
            RETURN node.id AS id,
                   node.name AS name,
                   node.price_min AS price,
                   node.currency AS currency,
                   score
            LIMIT $limit
            """,
            query=query,
            limit=limit,
        )
        return result.data()


def related_products(product_id: str, limit: int = 10) -> list[dict]:
    with _session() as session:
        result = session.run(
            """
            MATCH (p:Product {id: $id})
                  -[:IN_CATEGORY|HAS_ATTRIBUTE]->
                  (shared)
                  <-[:IN_CATEGORY|HAS_ATTRIBUTE]-
                  (other:Product)
            WHERE other.id <> p.id
              AND coalesce(other.is_active, false) = true
            WITH other, count(DISTINCT shared) AS shared_count
            RETURN other.id AS id,
                   other.name AS name,
                   other.price_min AS price,
                   other.currency AS currency,
                   shared_count
            ORDER BY shared_count DESC
            LIMIT $limit
            """,
            id=product_id,
            limit=limit,
        )
        return result.data()


def compare_products(product_id_a: str, product_id_b: str) -> dict:
    with _session() as session:
        result = session.run(
            """
            MATCH (a:Product {id: $a_id}), (b:Product {id: $b_id})
            OPTIONAL MATCH (a)-[:HAS_ATTRIBUTE]->(xa:AttributeValue)
            OPTIONAL MATCH (b)-[:HAS_ATTRIBUTE]->(xb:AttributeValue)
            RETURN a.name AS a_name,
                   b.name AS b_name,
                   collect(DISTINCT {key: xa.key, value: xa.value}) AS a_attributes,
                   collect(DISTINCT {key: xb.key, value: xb.value}) AS b_attributes
            """,
            a_id=product_id_a,
            b_id=product_id_b,
        )
        row = result.single()
        return row.data() if row else {}


def product_neighborhood(product_id: str, limit: int = 20) -> list[dict]:
    with _session() as session:
        result = session.run(
            """
            MATCH (p:Product {id: $id})-[*1..2]-(other:Product)
            WHERE other.id <> p.id
              AND coalesce(other.is_active, false) = true
            RETURN DISTINCT other.id AS id,
                            other.name AS name,
                            other.price_min AS price,
                            other.currency AS currency
            LIMIT $limit
            """,
            id=product_id,
            limit=limit,
        )
        return result.data()


if __name__ == "__main__":
    print("FULLTEXT:", search_products_fulltext("Tee", 5))
