# nodes/llm_node.py

from .base_node import Node
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from typing import Dict, Any
import time

class LLMNode(Node):
    def __init__(self, node_id: str, config: Dict[str, Any]):
        super().__init__(node_id, config)
        
        # 从config读取GPT模型、API key等
        self.model = config.get("model", "gpt-4-turbo-preview")
        self.temperature = config.get("temperature", 0.7)
        self.base_url = config.get("base_url", "https://api.chatanywhere.tech/v1")
        self.prompt_template = config.get("prompt_template", "{user_query}")
        
        # 初始化ChatOpenAI
        self.llm = ChatOpenAI(
            model=self.model,
            temperature=self.temperature,
            base_url=self.base_url
        )

        if self.prompt_template:
            self.prompt = ChatPromptTemplate.from_messages([
                ("system", self.prompt_template)
            ])

    def process(self, data: dict) -> dict:
        """
        用context和original_user_query组合prompt，调用LLM生成回答
        """
        context = data.get("context", "")
        request_id = str(int(time.time() * 1000))

        # 使用prompt模板生成完整prompt
        formatted_prompt = self.prompt.format(
            context=context,
            user_query=data.get("user_query", "")
        )

        response = self.llm.invoke(formatted_prompt)
        
        # 确保response是字符串
        answer = response.content if hasattr(response, 'content') else str(response)

        return {
            "answer": answer,
            "request_id": request_id
        }
    

