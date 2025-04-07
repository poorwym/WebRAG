# flow.py

import os
import sys
# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nodes.embedding_node import EmbeddingNode
from nodes.vectordb_node import VectorDBNode
from nodes.retriever_node import RetrieverNode
from nodes.llm_node import LLMNode
from nodes.output_node import OutputNode
from nodes.api_query_node import APIQueryNode

from utils.config_loader import ConfigLoader
from conversations_manager import ConversationsManager
from datetime import datetime

def generate_title(conversation_id, context):
    config = ConfigLoader()
    title_generator_model = config.get("title_generator.model")
    title_generator_prompt_template = config.get("title_generator.prompt_template")
    title_generator_api_key = config.get("title_generator.openai_api_key")
    title_generator_base_url = config.get("title_generator.base_url")
    title_generator_node = LLMNode(node_id="title_generator_node", config={"model": title_generator_model, "base_url": title_generator_base_url, "prompt_template": title_generator_prompt_template, "api_key": title_generator_api_key})
    input_data = {
        "context": context,
        "user_query": ""
    }
    data_after_llm = title_generator_node.process(input_data)
    title = data_after_llm["answer"]
    print("生成标题:", title)
    return title


# 添加用于从GUI调用的函数
def process_query(query, status_callback=None, progress_callback=None, conversation_id=None):
    """
    处理用户查询并返回结果
    
    参数:
    query: 用户输入的查询
    status_callback: 状态更新回调函数，接收状态文本
    progress_callback: 进度更新回调函数，接收进度百分比
    conversation_id: 对话id
    
    返回:
    final_output: 最终输出结果
    """
    # 更新状态
    if status_callback: status_callback("正在分析问题...")
    if progress_callback: progress_callback(10)

    # 获取对话管理器
    conversations_manager = ConversationsManager()
    
    # 如果conversation_id为None，创建新对话
    if conversation_id is None:
        conversation_id = conversations_manager.create_new_conversation()
        print("创建新对话:", conversation_id)
    
    # 获取对话
    conversation = conversations_manager.get_conversation(conversation_id)
    if conversation is None:
        # 如果对话不存在，创建新对话
        conversation_id = conversations_manager.create_new_conversation()
        conversation = conversations_manager.get_conversation(conversation_id)
        print("对话不存在，创建新对话:", conversation_id)
    
    # 获取对话中的消息
    title = conversation.get("title", "新对话")
    messages = conversation.get("messages", [])

    print("当前位于对话:", conversation_id)
    print("当前对话消息:", messages)

    context = ""
    
    for message in messages:
        context += f"{message.get('role')}: {message.get('content')}\n"

    if(len(context) > 10005):
        context = context[-10000:]
    config = ConfigLoader()
    # 获取 LLM 模型名
    llm_model_name = config.get("llm.model")
    # 获取 embedding 模型名
    embedding_model_name = config.get("embedding.model")
    # 获取 API 基础 URL
    base_url = config.get("llm.base_url")
    # 获取 prompt 模板
    prompt_template = config.get("llm.prompt_template")
    # 获取向量库存储路径（返回绝对路径）
    persist_dir = config.get_path("vectordb.persist_directory")
    # 获取 API key（环境变量自动解析）
    api_key = config.get("llm.openai_api_key")

    # 初始化各节点
    api_query_node = APIQueryNode(
        node_id="api_query_node", 
        config={
            "model": llm_model_name,
            "base_url": base_url,
            "prompt_template": prompt_template,
            "api_key": api_key
        }
    )
    # 嵌入节点
    embedding_node = EmbeddingNode(
        node_id="embedding_node",
        config={
            "model": embedding_model_name,
            "base_url": base_url,
            "api_key": api_key
        }
    )
    # 向量数据库节点
    vectordb_node = VectorDBNode(
        node_id="vectordb_node",
        config={
            "model": embedding_model_name,
            "persist_directory": persist_dir,
            "base_url": base_url,
            "api_key": api_key
        }
    )
    # 检索节点
    retriever_node = RetrieverNode(
        node_id="retriever_node"
    )
    # LLM节点
    llm_node = LLMNode(
        node_id="llm_node",
        config={
            "model": llm_model_name,
            "base_url": base_url,
            "prompt_template": prompt_template,
            "api_key": api_key
        }
    )
    # 输出节点
    output_node = OutputNode(
        node_id="output_node"
    )

    # 构造输入
    input_data = {
        "context": context,
        "user_query": query,
    }

    original_user_query = query

    # 按顺序执行
    if status_callback: status_callback("正在查询相关API...")
    if progress_callback: progress_callback(20)
    try:
        data_after_api_query = api_query_node.process(input_data)
    except Exception as e:
        print(f"API查询失败: {e}")
        return "API查询失败"

    if status_callback: status_callback("正在生成嵌入向量...")
    if progress_callback: progress_callback(40)
    api_description = data_after_api_query["api_description"]
    try:
        data_after_embedding = embedding_node.process({"api_description": api_description})
    except Exception as e:
        print(f"嵌入向量生成失败: {e}")
        return "嵌入向量生成失败"
    
    if status_callback: status_callback("正在向量数据库中检索相关文档...")
    if progress_callback: progress_callback(60)
    embeddings = data_after_embedding["embeddings"]
    try:
        data_after_vdb = vectordb_node.process({"embeddings": embeddings})
    except Exception as e:
        print(f"向量数据库检索失败: {e}")
        return "向量数据库检索失败"
    
    if status_callback: status_callback("正在处理检索结果...")
    if progress_callback: progress_callback(70)
    retrieved_docs = data_after_vdb["retrieved_docs"]
    try:
        data_after_retriever = retriever_node.process({"retrieved_docs": retrieved_docs})
    except Exception as e:
        print(f"检索结果处理失败: {e}")
        return "检索结果处理失败"
    
    if status_callback: status_callback("AI正在生成回答...")
    if progress_callback: progress_callback(80)
    context += f"检索结果: {data_after_retriever['context']}\n"
    try:
        data_after_llm = llm_node.process({"context": context, "user_query": original_user_query})
    except Exception as e:
        print(f"LLM生成失败: {e}")
        return "LLM生成失败"
    
    if progress_callback: progress_callback(95)
    try:
        final_result = output_node.process({"input": data_after_llm["answer"]})
    except Exception as e:
        print(f"输出处理失败: {e}")
        return "输出处理失败"

    # 更新对话
    conversations_manager.update_conversation(conversation_id, {
        "messages": [
            *messages,
            {"role": "user", "content": original_user_query, "timestamp": datetime.now().isoformat()},
            {"role": "assistant", "content": final_result["final_output"], "timestamp": datetime.now().isoformat()}
        ]
    })

    # 检查标题是否需要更新
    if title and title.startswith("新对话"):
        # 更新对话标题
        new_title = generate_title(conversation_id, original_user_query+"\n"+final_result["final_output"])
        conversations_manager.change_conversation_title_by_id(conversation_id, new_title)
    if progress_callback: progress_callback(100)
    print("="*100)
    return final_result["final_output"]

def status_callback(status_text):
    """
    处理用户查询并返回结果，同时更新状态和进度
    
    参数:
    status_text: 状态文本
    """
    print(status_text)

def progress_callback(progress):
    """
    处理用户查询并返回结果，同时更新状态和进度
    
    参数:
    progress: 进度百分比
    """
    print(f"进度: {progress}%")

if __name__ == "__main__":
    while True:
        # 初始化对话管理器
        conversations_manager = ConversationsManager()
        # 获取所有对话
        all_conversations = conversations_manager.get_all_conversations()
        # 打印所有对话的标题
        for conversation in all_conversations:
            print("id:", conversation.get("id"))
            print("title:", conversation.get("title"))
            print("="*100)
        conversation_id = str(input("请输入对话id(没有默认创建新对话):"))
        if conversation_id == "":
            conversation_id = conversations_manager.create_new_conversation()
        query = str(input("请输入你的问题："))
        result = process_query(query, status_callback, progress_callback, conversation_id)
        print(result)