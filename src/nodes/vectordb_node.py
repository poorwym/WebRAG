# nodes/vectordb_node.py

from .base_node import Node
from langchain_chroma import Chroma
import os
# import你的Chroma类或其它向量数据库
class VectorDBNode(Node):
    def __init__(self, node_id: str, config: dict = None):
        """
        用于连接向量数据库(如Chroma)的节点。
        """
        super().__init__(node_id, config)
        persist_directory = os.path.join(config.get("persist_directory"), config.get("model"))

        if not os.path.exists(persist_directory):
            raise ValueError(f"向量数据库不存在: {persist_directory}")
        else:
            print(f"向量数据库存在: {persist_directory}")
        
        # 初始化你的向量数据库, 例如Chroma
        self.vectordb = Chroma(
            persist_directory=persist_directory,
            embedding_function=None  # 如果需要，也可以放这里
        )

    def process(self, data: dict) -> dict:
        """
        1. 从data中获取embeddings
        2. 用于在VectorDB中进行相似度检索
        3. 返回检索到的文档
        """
        embeddings = data.get("embeddings")
        
        if embeddings is None:
            raise ValueError("No embeddings found in input data.")

        # 在Chroma中检索k条最相似文档
        docs = []
        for embedding in embeddings:
            docs.extend(self.vectordb.similarity_search_by_vector(embedding, k=3))
        
        return {
            "retrieved_docs": docs,
        }