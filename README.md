# Cesium RAG 助手

基于Cesium API文档的检索增强生成(RAG)问答系统，带有图形用户界面。

## 功能特点

- 基于OpenAI embeddings和GPT模型构建的RAG系统
- 通过向量数据库检索Cesium API相关文档
- 友好的PyQt5图形用户界面
- 黑暗主题和现代化UI设计

## 环境安装

本项目使用Conda管理环境，请确保安装了Anaconda或Miniconda后，
在CesiumRAG目录执行以下命令：

```bash
# 创建并激活conda环境
conda env create -f configs/environment.yml
conda activate webrag
```

创建环境变量 OPENAI_API_KEY，值为openai的apikey。
（可以在当前目录建立.env文件）

## 配置文件

项目使用`config.json`进行配置，主要包含以下设置：

- API密钥: 设置OpenAI API密钥
- 模型选择: 设置embedding和LLM模型
- 向量数据库: 设置Chroma持久化目录

请在运行程序前确保已正确配置`config.json`。
（默认使用了可怜的wym的apikey，要配置自己的可以参考[nodes文档](doc/nodes.md)）

### 可用模型配置

配置文件中包含多种预设的模型配置：

- GPT系列: gpt-3.5-turbo, gpt-4, gpt-4.5-preview等
- OpenAI O系列: o1-mini, o1-preview, o3-mini, o1等
- 其他模型: Claude, Gemini, DeepSeek, Grok等

可以根据需要在`configs/config.json`中选择和配置适合的模型。

## 使用方法

### 构建向量数据库

在首次使用前，需要构建向量数据库,默认数据存在data/curated/目录下：

```bash
python src/build_db.py
```

### 命令行交互模式

```bash
python src/flow.py
```

### 图形用户界面模式

```bash
python src/gui.py
```

## 系统架构

系统由以下几个主要节点组成：

1. APIQueryNode - 分析用户查询中可能涉及的API
2. EmbeddingNode - 将API描述转换为向量表示
3. VectorDBNode - 在向量数据库中检索相关文档
4. RetrieverNode - 处理检索到的文档
5. LLMNode - 生成回答
6. OutputNode - 处理最终输出

