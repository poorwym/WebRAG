# nodes/retriever_node.py

from .base_node import Node
from utils.logger import Logger
from utils.config_loader import ConfigLoader
import os

class RetrieverNode(Node):
    def __init__(self, node_id: str, config: dict = None):
        super().__init__(node_id, config)
        self.logger = Logger.get_logger("flow")
        self.config = ConfigLoader()
        # 可根据需要存一些额外的处理配置

    def process(self, data: dict) -> dict:
        """
        对检索到的文档进行拼接/摘要或其他处理，并返回给LLM使用。
        """
        retrieved_docs = data.get("retrieved_docs", [])
        self.logger.info(f"检索到的文档: {retrieved_docs}")
        context = ""

        for doc in retrieved_docs:
            context += f"## {doc.page_content}\n\n"
        
        self.logger.info(f"拼接后的上下文: {context}")

        return {
            "context": context,
        }