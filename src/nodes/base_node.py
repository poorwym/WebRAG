# nodes/base_node.py
from abc import ABC, abstractmethod

class Node(ABC):
    def __init__(self, node_id: str, config: dict = None):
        """
        节点的初始化方法。
        :param node_id: 节点的唯一标识（字符串）。
        :param config: 节点的配置字典,可以包含模型名称、API Key等。
        """
        self.node_id = node_id
        self.config = config or {}

    @abstractmethod
    def process(self, data: dict) -> dict:
        """
        每个节点必须实现的处理方法。
        :param data: 来自上一个节点或外部的数据输入。
        :return: 输出处理后的结果，通常是 dict。
        """
        pass

    def print_config(self):
        print(self.config)
    
    def print_node_id(self):
        print(self.node_id)
