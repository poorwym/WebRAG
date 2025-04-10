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
    
    def _get_path(self, path: str):
        unix_path = path.replace("\\", "/")
        path_list = unix_path.split("/")[-5:]
        project_root = self.config.project_root
        normalized_path = os.path.join(project_root, *path_list)
        return normalized_path

    def process(self, data: dict) -> dict:
        """
        对检索到的文档进行拼接/摘要或其他处理，并返回给LLM使用。
        """
        retrieved_docs = data.get("retrieved_docs", [])
        self.logger.info(f"检索到的文档: {retrieved_docs}")
        context = ""

        '''
        for doc in retrieved_docs:
            context += f"## {doc.page_content}\n\n"
        '''
        for doc in retrieved_docs:
            path = doc.metadata.get("source", "")
            normalized_path = self._get_path(path)
            try:
                with open(normalized_path, "r", encoding="utf-8") as f:
                    content = f.read()
                context += f"## {content}\n\n"
            except Exception as e:
                self.logger.error(f"读取文件失败: {e}")
                context += f"## 文件读取失败: {e}\n\n"
        
        # self.logger.info(f"拼接后的上下文: {context}")

        return {
            "context": context,
        }