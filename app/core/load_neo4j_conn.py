import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()


class LoadNeo4jConn:
    _driver = None

    @classmethod
    def get_driver(cls):
        if cls._driver is None:
            cls._driver = GraphDatabase.driver(
                os.getenv("NEO4J_URI"),
                auth=(
                    os.getenv("NEO4J_USER"),
                    os.getenv("NEO4J_PASSWORD"),
                ),
            )
        return cls._driver

    @classmethod
    def database(cls) -> str:
        return os.getenv("NEO4J_DATABASE", "neo4j")

    @classmethod
    def verify(cls):
        cls.get_driver().verify_connectivity()

    @classmethod
    def close(cls):
        if cls._driver is not None:
            cls._driver.close()
            cls._driver = None
