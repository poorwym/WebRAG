# nodes/retriever_node.py

from .base_node import Node

class RetrieverNode(Node):
    def __init__(self, node_id: str, config: dict = None):
        super().__init__(node_id, config)
        # 可根据需要存一些额外的处理配置

    def process(self, data: dict) -> dict:
        """
        对检索到的文档进行拼接/摘要或其他处理，并返回给LLM使用。
        """
        retrieved_docs = data.get("retrieved_docs", [])

        # 简单示例：将文档内容拼接为字符串
        context = "\n".join([doc.page_content for doc in retrieved_docs])

        return {
            "context": context,
        }