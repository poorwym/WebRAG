# 数据库模块文档

## 概述

数据库模块负责处理网页内容的抓取、处理和向量化存储。主要包含以下几个组件：

1. 链接提取器（`extract_links.py`）
2. 下载器（`downloader.py`）
3. 内容整理器（`curator.py`）
4. 向量化器（`vectorizator.py`）
5. 数据库初始化（`init_db.py`）

## 目录结构

数据库文件存储在 `data/database/{db_name}/` 目录下，包含以下子目录：

- `downloaded_sites/`: 存储下载的原始网页
- `curated/`: 存储处理后的Markdown文件
- `chroma_openai/`: 存储向量数据库
- `urls/`: 存储URL相关文件
  - `extracted_links.txt`: 提取的链接
  - `error_links.txt`: 错误的链接
  - `urls_to_extract.txt`: 待提取的链接

## 组件说明

### 1. 链接提取器（LinksExtractor）

负责从指定网站提取相关链接。

主要功能：
- 支持多线程并行爬取
- 可配置爬取深度
- 自动去重和错误处理
- 支持断点续传

使用方法：
```python
extractor = LinksExtractor(db_name="cesium", max_depth=3, num_threads=20)
extractor.process(required_prefix="https://cesium.com/learn/")
```

### 2. 下载器（SimpleAsyncDownloader）

负责异步下载网页内容。

主要功能：
- 异步并发下载
- 支持限速和重试
- 自动跳过已下载文件
- 错误处理和日志记录

使用方法：
```python
downloader = SimpleAsyncDownloader(delay=1.0, max_connections=10, db_name="cesium")
downloader.run(url_list_file)
```

### 3. 内容整理器（PageCurator）

负责将HTML内容转换为Markdown格式。

主要功能：
- HTML清理和优化
- 自动提取主要内容
- 转换为Markdown格式
- 多线程并行处理

使用方法：
```python
curator = PageCurator(input_dir, config, db_name="cesium")
curator.process_directory(max_workers=8)
```

### 4. 向量化器（Vectorizator）

负责将文本内容转换为向量并存储。

主要功能：
- 支持多种文档格式（txt, pdf, docx, md）
- 文本分块处理
- 向量化存储
- 支持多种嵌入模型

使用方法：
```python
vectorizator = Vectorizator(config, db_name="cesium", embeddings_model=model)
vectorizator.process()
```

### 5. 数据库初始化（init_db）

负责创建数据库目录结构。

主要功能：
- 创建必要的目录结构
- 初始化必要的文件

使用方法：
```python
init_db("cesium")
```

## 使用流程

1. 初始化数据库：
```python
init_db("cesium")
```

2. 提取链接：
```python
extractor = LinksExtractor("cesium")
extractor.process()
```

3. 下载网页：
```python
downloader = SimpleAsyncDownloader(db_name="cesium")
downloader.run(url_list_file)
```

4. 处理内容：
```python
curator = PageCurator(input_dir, config, db_name="cesium")
curator.process_directory()
```

5. 向量化存储：
```python
vectorizator = Vectorizator(config, db_name="cesium", embeddings_model=model)
vectorizator.process()
```

## 注意事项

1. 确保已安装所有必要的依赖包
2. 配置正确的API密钥和基础URL
3. 注意爬取频率，避免对目标网站造成压力
4. 定期备份重要数据
5. 监控错误日志，及时处理异常情况
