# nodes/output_node.py

from .base_node import Node

class OutputNode(Node):
    def __init__(self, node_id: str, config: dict = None):
        super().__init__(node_id, config)

    def process(self, data: dict) -> dict:
        """
        最终输出节点，可进行格式化或直接返回给前端
        """
        answer = data.get("input", "")
        
        # 这里可以做一些后处理，例如Markdown转换，或加上系统回答前缀等等
        final_output = f"{answer}"

        return {
            "final_output": final_output
        }