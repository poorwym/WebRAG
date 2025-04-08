#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
from langchain_community.document_loaders import DirectoryLoader, TextLoader, UnstructuredPDFLoader, UnstructuredWordDocumentLoader, UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
import openai
import sys

# 添加项目根目录到系统路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from src.utils.logger import Logger

class Vectorizator:
    def __init__(self, config, db_name, embeddings_model):
        self.config = config
        self.db_name = db_name
        self.embeddings_model = embeddings_model
        self.logger = Logger("vectorizator")
        
        # 设置 OpenAI API 密钥和基础 URL
        openai.base_url = "https://api.chatanywhere.tech/v1"
        
        # 设置路径
        self.folder_path = os.path.join(config.project_root, "data", "database", db_name, "curated")
        self.persist_path = os.path.join(config.project_root, "data", "database", db_name, "chroma_openai", embeddings_model['model'])

    def load_documents_from_folder(self, folder_path):
        self.logger.info(f"开始扫描目录: {folder_path}")
        loaders = [
            DirectoryLoader(folder_path, glob="**/*.txt", loader_cls=TextLoader, show_progress=True),
            DirectoryLoader(folder_path, glob="**/*.pdf", loader_cls=UnstructuredPDFLoader, show_progress=True),
            DirectoryLoader(folder_path, glob="**/*.docx", loader_cls=UnstructuredWordDocumentLoader, show_progress=True),
            DirectoryLoader(folder_path, glob="**/*.md", loader_cls=TextLoader, show_progress=True),
        ]
        all_docs = []
        for loader in loaders:
            try:
                docs = loader.load()
                self.logger.info(f"使用 {loader.__class__.__name__} 加载了 {len(docs)} 篇文档")
                all_docs.extend(docs)
            except Exception as e:
                self.logger.error(f"使用 {loader.__class__.__name__} 加载文档时出错: {str(e)}")
        return all_docs

    def split_documents(self, docs, chunk_size=500, chunk_overlap=50):
        splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        return splitter.split_documents(docs)

    def build_vectorstore(self, docs, persist_path, embeddings_model):
        embeddings = OpenAIEmbeddings(
            model=embeddings_model,
            base_url="https://api.chatanywhere.tech/v1",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        vectordb = Chroma.from_documents(documents=docs, embedding=embeddings, persist_directory=persist_path)
        vectordb.persist()
        return vectordb

    def process(self):
        # 检查向量数据库是否已存在
        if os.path.exists(self.persist_path):
            self.logger.warning("向量数据库已存在，请选择是否删除[y/N]")
            choice = input("请输入你的选择: ")
            if choice == "y":
                shutil.rmtree(self.persist_path)
                self.logger.info("向量数据库已删除")
            else:
                self.logger.info("已取消删除")
                return

        if not os.path.exists(self.folder_path):
            self.logger.error(f"文件夹 {self.folder_path} 不存在")
            return

        self.logger.info(f"embeddings_model: {self.embeddings_model}")
        self.logger.info(f"folder_path: {str(self.folder_path)}")
        self.logger.info(f"persist_path: {str(self.persist_path)}")

        self.logger.info("加载文件...")
        raw_docs = self.load_documents_from_folder(self.folder_path)

        self.logger.info(f"共加载 {len(raw_docs)} 篇文档，开始切分...")
        split_docs = self.split_documents(raw_docs)

        self.logger.info(f"共切分为 {len(split_docs)} 段，开始构建向量库并持久化...")
        self.build_vectorstore(split_docs, self.persist_path, self.embeddings_model['model'])

        self.logger.info("构建完毕，向量数据库已持久化。")

def process(db_name: str, embeddings_model: dict):
    from src.utils.config_loader import ConfigLoader
    config = ConfigLoader()
    vectorizator = Vectorizator(config, db_name, embeddings_model)
    vectorizator.process()

if __name__ == "__main__":
    from src.utils.config_loader import ConfigLoader
    config = ConfigLoader()
    
    logger = Logger("vectorizator")
    logger.info("请选择embedding模型:")
    for i, embedding_model in enumerate(config.embedding_model_list):
        print(f"{i}: {embedding_model}")

    embedding_model_name = str(input("请输入你的选择: "))
    if embedding_model_name not in config.embedding_model_list:
        logger.error("embedding_model_name 不存在")
        exit()

    embeddings_model = config.embedding_model_list[embedding_model_name]
    logger.info(f"embeddings_model: {embeddings_model}")

    db_name = str(input("请输入向量数据库名称: "))
    logger.info(f"db_name: {db_name}")

    process(db_name, embeddings_model)
