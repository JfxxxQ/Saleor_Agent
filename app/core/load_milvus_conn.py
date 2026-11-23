from sentence_transformers import SentenceTransformer
from pymilvus import MilvusClient
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class LoadMilvusConn:
    _milvus_client = None
    _embedding_model = None

    @staticmethod
    def load_embedding_model():
        if LoadMilvusConn._embedding_model is None:
            LoadMilvusConn._embedding_model = SentenceTransformer(
                model_name_or_path=os.getenv("BGE_MODEL_PATH"),
                device=os.getenv("BGE_DEVICE"),
                local_files_only=True,
            )
        return LoadMilvusConn._embedding_model


    # 加载向量数据库连接对象
    @staticmethod
    def load_milvus_conn():
        if LoadMilvusConn._milvus_client is None:
            Path(os.getenv("MILVUS_LOCAL_PATH")).parent.mkdir(
                parents=True, exist_ok=True
            )
            LoadMilvusConn._milvus_client = MilvusClient(
                uri=os.getenv("MILVUS_LOCAL_PATH")
            )
        return LoadMilvusConn._milvus_client

    @staticmethod
    def close_milvus_conn():
        if LoadMilvusConn._milvus_client is not None:
            LoadMilvusConn._milvus_client.close()
            LoadMilvusConn._milvus_client = None

    @staticmethod
    def embedding_dim() -> int:
        model = LoadMilvusConn.load_embedding_model()
        get_dim = getattr(model, "get_embedding_dimension", None)
        if get_dim is not None:
            return get_dim()
        return model.get_sentence_embedding_dimension()

    @staticmethod
    def embed_documents(texts: list[str]) -> list[list[float]]:
        return LoadMilvusConn.load_embedding_model().encode(
            texts,
            normalize_embeddings=True,
            batch_size=32,
            show_progress_bar=False,
        ).tolist()

    @staticmethod
    def embed_query(text: str) -> list[float]:
        # BGE v1.5 检索建议加查询指令；如果文档侧不加，查询侧可以加。
        # 是否加要保持一致，建议做成配置项。
        # text = "为这个句子生成表示以用于检索相关文章：" + text
        return LoadMilvusConn.load_embedding_model().encode(
            [text],
            normalize_embeddings=True,
        )[0].tolist()