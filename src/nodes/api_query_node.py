from .llm_node import LLMNode
from langchain.prompts import PromptTemplate
import time
from utils.logger import Logger

class APIQueryNode(LLMNode):
    def __init__(self, node_id: str, config: dict = None):
        super().__init__(node_id, config)
        self.db_name = config.get("db_name", "")
        # 设置专门用于 API 查询的 prompt 模板
        self.prompt_template = """请分析以下用户查询中可能涉及到的{db_name}API，
            不同api间用逗号间隔。
            只关注 API 相关的部分，不需要其他解释。
            示例：
            “a api, b api, c api”
            输出所有可能的api，即使在你的印象里这些api是不存在的。

            用户查询:
            {user_query}
            上下文:
            {context}
            """
        
        # 初始化 prompt 模板，确保使用user_query和db_name作为输入变量
        self.prompt = PromptTemplate(
            template=self.prompt_template,
            input_variables=["user_query", "db_name", "context"]
        )

        self.logger = Logger.get_logger("flow")

    def process(self, data: dict) -> dict:
        """
        处理用户查询，提取 API 相关的描述
        """
        user_query = data.get("user_query", "")
        context = data.get("context", "")
        request_id = str(int(time.time() * 1000))
        
        # 使用 prompt 模板生成完整 prompt
        formatted_prompt = self.prompt.format(
            user_query=user_query,
            db_name=self.db_name,
            context=context
        )

        # 直接使用继承自LLMNode的llm对象，但使用我们自己的prompt
        response = self.llm.invoke(formatted_prompt)
        
        # 确保response是字符串
        api_description = response.content if hasattr(response, 'content') else str(response)
        self.logger.info(f"API描述: {api_description}")
        # 将原始查询和 API 描述一起返回
        return {
            "api_description": api_description,
            "answer": api_description,
            "request_id": request_id
        } 