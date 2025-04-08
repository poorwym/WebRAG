import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader, UnstructuredPDFLoader, UnstructuredWordDocumentLoader, UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
import openai
import shutil
from utils.logger import Logger

# 设置 OpenAI API 密钥和基础 URL
openai.base_url = "https://api.chatanywhere.tech/v1"

# 创建logger实例
logger = Logger("build_db")

# 1. 加载文件夹中的所有文档
def load_documents_from_folder(folder_path):
    logger.info(f"开始扫描目录: {folder_path}")
    loaders = [
        DirectoryLoader(folder_path, glob="**/*.txt", loader_cls=TextLoader, show_progress=True),
        DirectoryLoader(folder_path, glob="**/*.pdf", loader_cls=UnstructuredPDFLoader, show_progress=True),
        DirectoryLoader(folder_path, glob="**/*.docx", loader_cls=UnstructuredWordDocumentLoader, show_progress=True),
        DirectoryLoader(folder_path, glob="**/*.md", loader_cls=UnstructuredMarkdownLoader, show_progress=True),
    ]
    all_docs = []
    for loader in loaders:
        try:
            docs = loader.load()
            logger.info(f"使用 {loader.__class__.__name__} 加载了 {len(docs)} 篇文档")
            all_docs.extend(docs)
        except Exception as e:
            logger.error(f"使用 {loader.__class__.__name__} 加载文档时出错: {str(e)}")
    return all_docs

# 2. 分割文档
def split_documents(docs, chunk_size=500, chunk_overlap=50):
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_documents(docs)

# 3. 构建 embedding 并持久化
def build_vectorstore(docs, persist_path, embeddings_model):
    embeddings = OpenAIEmbeddings(
        model=embeddings_model,
        base_url="https://api.chatanywhere.tech/v1",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    vectordb = Chroma.from_documents(documents=docs, embedding=embeddings, persist_directory=persist_path)
    vectordb.persist()
    return vectordb

from utils.config_loader import ConfigLoader

config = ConfigLoader()

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

'''
folder_name = str(input("请输入文件夹名称: "))
print("folder_name: ", folder_name)
'''

folder_path = os.path.join(config.project_root, "data", "curated", "cesium")
persist_path = os.path.join(config.project_root, "data", "chroma_openai", db_name, embeddings_model['model'])
if os.path.exists(persist_path):
    logger.warning("向量数据库已存在，请选择是否删除[y/N]")
    choice = input("请输入你的选择: ")
    if choice == "y":
        shutil.rmtree(persist_path)
        logger.info("向量数据库已删除")
    else:
        logger.info("已取消删除")
        exit()

if not os.path.exists(folder_path):
    logger.error(f"文件夹 {folder_path} 不存在")
    exit()

logger.info(f"embeddings_model: {embeddings_model}")
logger.info(f"folder_path: {str(folder_path)}")
logger.info(f"persist_path: {str(persist_path)}")


logger.info("加载文件...")
raw_docs = load_documents_from_folder(folder_path)

logger.info(f"共加载 {len(raw_docs)} 篇文档，开始切分...")
split_docs = split_documents(raw_docs)

logger.info(f"共切分为 {len(split_docs)} 段，开始构建向量库并持久化...")
build_vectorstore(split_docs, persist_path, embeddings_model['model'])

logger.info("构建完毕，向量数据库已持久化。")