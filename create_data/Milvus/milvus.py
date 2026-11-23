import os
from pathlib import Path
from pymilvus import DataType, MilvusClient

BASE_DIR = Path(__file__).resolve().parents[2]
COLLECTION = os.getenv("MILVUS_COLLECTION", "products")
MILVUS_LOCAL_PATH = os.getenv(
    "MILVUS_LOCAL_PATH",
    str(BASE_DIR / "data" / "milvus_products.db"),
)
DIM = int(os.getenv("MILVUS_DIM", "1024"))

# http/https 开头是 Milvus Server，否则是 Milvus Lite 本地文件
IS_LITE = not MILVUS_LOCAL_PATH.startswith(("http://", "https://"))


def get_client() -> MilvusClient:
    return MilvusClient(uri=MILVUS_LOCAL_PATH)


def ensure_collection(client: MilvusClient):
    if client.has_collection(COLLECTION):
        # 已有的 collection 重新打开后可能处于 released 状态，查询前必须 load
        client.load_collection(COLLECTION)
        return

    schema = MilvusClient.create_schema(
        auto_id=False,
        enable_dynamic_field=False,
    )

    schema.add_field("id", DataType.VARCHAR, is_primary=True, max_length=128)
    schema.add_field("product_id", DataType.VARCHAR, max_length=64)
    schema.add_field("channel", DataType.VARCHAR, max_length=64)
    schema.add_field("name", DataType.VARCHAR, max_length=512)
    schema.add_field("description", DataType.VARCHAR, max_length=8192)
    schema.add_field("category", DataType.VARCHAR, max_length=256)
    schema.add_field("product_type", DataType.VARCHAR, max_length=256)
    schema.add_field("brand", DataType.VARCHAR, max_length=256)
    schema.add_field("price_min", DataType.FLOAT)
    schema.add_field("price_max", DataType.FLOAT)
    schema.add_field("currency", DataType.VARCHAR, max_length=8)
    schema.add_field("image_url", DataType.VARCHAR, max_length=1024)
    schema.add_field("variants_json", DataType.JSON)
    schema.add_field("updated_at", DataType.INT64)
    schema.add_field("is_active", DataType.BOOL)
    schema.add_field("embedding", DataType.FLOAT_VECTOR, dim=DIM)

    index_params = client.prepare_index_params()

    # AUTOINDEX 在 Lite 和 Standalone 都能用
    index_params.add_index(
        field_name="embedding",
        index_type="AUTOINDEX",
        metric_type="COSINE",
    )

    # 标量索引 Lite 不一定支持，只在 Standalone 加
    if not IS_LITE:
        index_params.add_index(field_name="channel", index_type="INVERTED")
        index_params.add_index(field_name="category", index_type="INVERTED")
        index_params.add_index(field_name="product_type", index_type="INVERTED")
        index_params.add_index(field_name="is_active", index_type="INVERTED")

    client.create_collection(
        collection_name=COLLECTION,
        schema=schema,
        index_params=index_params,
    )

    # Lite 和 Server 都需要 load 后才能 search/query
    client.load_collection(COLLECTION)


def flush_collection(client: MilvusClient):
    # 同步后 flush，确保新写入的数据对后续查询可见
    client.flush(COLLECTION)
