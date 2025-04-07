# nodes/embedding_node.py

from .base_node import Node
from langchain_openai import OpenAIEmbeddings
from typing import Dict, Any
# 这里的 embedding 相关引入，例如 from langchain_openai import OpenAIEmbeddings
# 或者你自己封装的embedding类

class EmbeddingNode(Node):
    def __init__(self, node_id: str, config: Dict[str, Any]):
        """
        继承自BaseNode,初始化embedding相关。
        """
        super().__init__(node_id, config)
        # 在config中可能有 'model'、'openai_api_key' 等
        self.model = config.get("model", "text-embedding-3-small")
        self.base_url = config.get("base_url", "https://api.chatanywhere.tech/v1")
        self.embeddings = OpenAIEmbeddings(
            model=self.model,
            base_url=self.base_url
        )
        self.vectordb = None

    def process(self, data: dict) -> dict:
        """
        1. 从data中读取文本
        2. 调用 embedding_model 获取向量
        3. 返回新的dict
        """
        api_description = data.get("api_description", "")
        
        # 处理AIMessage对象
        if hasattr(api_description, 'content'):
            api_description = api_description.content

        if api_description == "无明确的 API 相关描述":
            return {
                "embeddings": [],
                "api_description": api_description
            }
        
        apis = api_description.split(",")
        embeddings = []
        for api in apis:
            embeddings.append(self.embeddings.embed_query(api))
        
        return {
            "embeddings": embeddings,
            "api_description": api_description
        }