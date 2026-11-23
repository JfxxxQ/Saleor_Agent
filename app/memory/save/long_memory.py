import chromadb
import os
from dotenv import load_dotenv
import uuid
from chromadb.utils import embedding_functions


#读取配置文件
load_dotenv()
"""
长期记忆，记忆存储用户的偏好信息，事实，任务等
"""
class LongMemory:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        #读取向量数据库
        self.client = chromadb.PersistentClient(path=os.getenv("CHROM_DB_URL"))
        # 加载本地中文向量模型（BGE 需要归一化 + CLS 池化，sentence-transformers 会自动处理）
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=os.getenv("BGE_MODEL_PATH"),
            device=os.getenv("BGE_DEVICE", "cpu"),
            normalize_embeddings=True,
        )
        #获取集合：显式使用 cosine 距离，与 BGE 的推荐用法一致
        self.collection = self.client.get_or_create_collection(
            name = os.getenv("CHROM_DB_NAME"),
            embedding_function= self.embedding_function,
            configuration={"hnsw": {"space": "cosine"}}
        )
        self._initialized = True

    def add_memory(self, agent_user_id, content:str, metadata=None):
        #设置向量数据库id保持唯一，用户id只有1个
        id = str(uuid.uuid4())
        extra = {
            k: v
            for k, v in (metadata or {}).items()
            if v is not None
        }
        meta = {
            "user_id": int(agent_user_id),
            "memory_type": "fact",
            "source": "stated",
            "status": "active",
            "confidence": 1.0,
            **extra,
        }
        self.collection.add(
            ids = [id],
            documents = [content],
            metadatas = [
                meta
            ]
        )
    #获取记忆
    #max_distance 为向量距离阈值，超过该值的检索结果会被过滤掉；为 None 时不过滤
    def load_memory(self, agent_user_id, question, n_results=3, max_distance=None):
        rs = self.collection.query(
            query_texts = [question],
            n_results = n_results,
            where = {
                "user_id":int(agent_user_id)
            },
            include = ["documents", "distances"]
        )
        documents = rs["documents"][0] if rs["documents"] else []
        distances = rs["distances"][0] if rs["distances"] else []
        if max_distance is None:
            return documents
        return [doc for doc, distance in zip(documents, distances) if distance <= max_distance]

#测试方法
def test():
    l = LongMemory()
    l.add_memory(1,"我正在学习langchain", {"id": str(uuid.uuid4())})
    l.add_memory(1, "我正在学习python", {"id": str(uuid.uuid4())})
    l.add_memory(1, "我喜欢看书", {"id": str(uuid.uuid4())})
    l.add_memory(1, "我正在学习向量数据库", {"id": str(uuid.uuid4())})

if __name__ =="__main__":
   test()
   l = LongMemory()
   rs = l.load_memory(1,"我喜欢什么")
   print(rs)