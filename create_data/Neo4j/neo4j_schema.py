from app.core.load_neo4j_conn import LoadNeo4jConn


SCHEMA_QUERIES = [
    """
    CREATE CONSTRAINT product_id IF NOT EXISTS
    FOR (p:Product) REQUIRE p.id IS UNIQUE
    """,
    """
    CREATE CONSTRAINT variant_id IF NOT EXISTS
    FOR (v:Variant) REQUIRE v.id IS UNIQUE
    """,
    """
    CREATE CONSTRAINT category_id IF NOT EXISTS
    FOR (c:Category) REQUIRE c.id IS UNIQUE
    """,
    """
    CREATE CONSTRAINT product_type_id IF NOT EXISTS
    FOR (t:ProductType) REQUIRE t.id IS UNIQUE
    """,
    """
    CREATE CONSTRAINT collection_id IF NOT EXISTS
    FOR (c:Collection) REQUIRE c.id IS UNIQUE
    """,
    """
    CREATE CONSTRAINT attribute_value_key IF NOT EXISTS
    FOR (a:AttributeValue) REQUIRE (a.key, a.value) IS UNIQUE
    """,
    """
    CREATE INDEX product_name IF NOT EXISTS
    FOR (p:Product) ON (p.name)
    """,
    """
    CREATE FULLTEXT INDEX product_fulltext IF NOT EXISTS
    FOR (p:Product) ON EACH [p.name, p.description]
    """,
]


def ensure_schema():
    driver = LoadNeo4jConn.get_driver()

    with driver.session(database=LoadNeo4jConn.database()) as session:
        for query in SCHEMA_QUERIES:
            session.run(query).consume()

    print("Neo4j schema ready")


if __name__ == "__main__":
    ensure_schema()
