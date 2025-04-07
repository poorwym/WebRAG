from .llm_node import LLMNode
from langchain.prompts import PromptTemplate
import time

class APIQueryNode(LLMNode):
    def __init__(self, node_id: str, config: dict = None):
        super().__init__(node_id, config)
        
        # 设置专门用于 API 查询的 prompt 模板
        self.prompt_template = """请分析以下用户查询中可能涉及到的 Cesium API，并用简短的陈述句表达出来，不同api间用逗号间隔。
            只关注 API 相关的部分，不需要其他解释。
            如果查询中没有明确的 API 相关描述，请返回"无明确的 API 相关描述"。

            用户查询:
            {user_query}

            请用陈述句表达:"""
        
        # 初始化 prompt 模板，确保只使用user_query作为输入变量
        self.prompt = PromptTemplate(
            template=self.prompt_template,
            input_variables=["user_query"]
        )

    def process(self, data: dict) -> dict:
        """
        处理用户查询，提取 API 相关的描述
        """
        user_query = data.get("user_query", "")
        request_id = str(int(time.time() * 1000))
        
        # 使用 prompt 模板生成完整 prompt
        formatted_prompt = self.prompt.format(
            user_query=user_query
        )

        # 直接使用继承自LLMNode的llm对象，但使用我们自己的prompt
        response = self.llm.invoke(formatted_prompt)
        
        # 确保response是字符串
        api_description = response.content if hasattr(response, 'content') else str(response)
        
        # 将原始查询和 API 描述一起返回
        return {
            "api_description": api_description,
            "answer": api_description,
            "request_id": request_id
        } 