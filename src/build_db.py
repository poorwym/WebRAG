#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from database.vectorizator import process
from database.downloader import SimpleAsyncDownloader
from database.curator import PageCurator
from database.init_db import init_db
from database.links_extractor import LinksExtractor
from utils.config_loader import ConfigLoader
from utils.logger import Logger
import argparse
import os
import asyncio

async def download_urls(db_name: str, file_path: str, delay: float = 1.0, max_connections: int = 10):
    """
    下载URL列表中的网页内容
    """
    downloader = SimpleAsyncDownloader(delay=delay, max_connections=max_connections, db_name=db_name)
    if os.path.exists(file_path):
        logger.info(f"开始从文件加载URL: {file_path}")
        await downloader.run(file_path)
    else:
        logger.error(f"文件不存在：{file_path}")
        raise FileNotFoundError(f"URL文件不存在：{file_path}")

async def build_rag_database(db_name: str, file_path: str, embeddings_model: str):
    """
    从URL文件构建RAG数据库的完整流程
    """
    logger = Logger("build_db")
    
    try:
        # 1. 初始化数据库目录结构
        logger.info("初始化数据库目录结构...")
        init_db(db_name)
        
        # 2. 提取URL
        logger.info("开始提取URL...")
        extractor = LinksExtractor(db_name=db_name, file_path=file_path, required_prefix="https://pro.arcgis.com/en/pro-app/3.4/")
        extractor.process()
        
        # 3. 下载网页内容
        logger.info("开始下载网页内容...")
        extracted_links_path = os.path.join("data", "database", db_name, "urls", "extracted_links.txt")
        await download_urls(db_name, extracted_links_path)
        
        # 4. 处理下载的内容
        logger.info("处理下载的内容...")
        input_dir = os.path.join("data", "database", db_name, "downloaded_sites")
        curator = PageCurator(input_dir, ConfigLoader(), db_name=db_name)
        curator.process_directory(max_workers=8)
        
        # 5. 向量化存储
        logger.info("开始向量化存储...")
        process(db_name, embeddings_model)
        
        logger.info("RAG数据库构建完成！")
        
    except Exception as e:
        logger.error(f"构建RAG数据库时发生错误: {str(e)}")
        raise

if __name__ == "__main__":
    config = ConfigLoader()
    logger = Logger("build_db")
    
    parser = argparse.ArgumentParser(description='Build RAG database')
    parser.add_argument('--db-name', type=str, default='cesium', help='用于构建数据库的名称')
    parser.add_argument('--file-path', type=str, default='data/database/cesium/urls/extracted_links.txt', help='包含URL的文件路径')
    args = parser.parse_args()
    
    db_name = args.db_name
    file_path = args.file_path
    
    logger.info(f"db_name: {db_name}")
    logger.info(f"file_path: {file_path}")
    
    # 选择embedding模型
    logger.info("请选择embedding模型:")
    for i, embedding_model in enumerate(config.embedding_model_list):
        print(f"{i}: {embedding_model}")

    embedding_model_name = str(input("请输入你的选择(输入完整模型名，例如text-embedding-3-small): "))
    if embedding_model_name not in config.embedding_model_list:
        logger.error("embedding_model_name 不存在")
        exit()

    embeddings_model = config.embedding_model_list[embedding_model_name]
    logger.info(f"embeddings_model: {embeddings_model}")

    # 执行完整的RAG数据库构建流程
    asyncio.run(build_rag_database(db_name, file_path, embeddings_model))