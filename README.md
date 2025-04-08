# WebRAG

WebRAG 是一个基于 RAG (Retrieval-Augmented Generation) 的网页内容检索和问答系统。该系统能够自动抓取、处理和存储网页内容，并通过向量检索和 LLM 生成来回答用户问题。

## 功能特性

- 自动网页内容抓取和处理
- 多线程并行爬取和下载
- 智能内容提取和向量化
- 基于向量检索的文档查询
- 大语言模型驱动的问答系统
- 模块化设计，易于扩展

## 系统架构

系统主要包含两个核心模块：

### 1. 数据库模块

负责网页内容的抓取、处理和向量化存储，包含以下组件：

- **链接提取器**：从指定网站提取相关链接
- **下载器**：异步下载网页内容
- **内容整理器**：将 HTML 转换为 Markdown
- **向量化器**：将文本转换为向量并存储
- **数据库初始化**：创建必要的目录结构

### 2. 节点模块

负责处理用户查询和生成回答，包含以下节点：

- **LLM节点**：调用大语言模型生成回答
- **API查询节点**：分析用户查询中的 API 相关描述
- **Embedding节点**：将文本转换为向量表示
- **向量数据库节点**：检索相似文档
- **检索器节点**：处理和格式化检索结果
- **输出节点**：格式化最终输出

## 安装说明

1. 克隆项目：
```bash
git clone https://github.com/yourusername/WebRAG.git
cd WebRAG
```

2. 安装依赖：
```bash
conda env create -f configs/environments.yml
conda activate webrag
python src/setup.py
```

3. 添加环境变量:
在configs/目录下创建.env文件。
内容如下：
```bash
OPENAI_API_KEY=your-api-key
```
默认的base_url为`https://api.chatanywhere.tech/v1`,购买方法详见[GPT_API_free](https://github.com/chatanywhere/GPT_API_free?tab=readme-ov-file).
## 使用方法
1. 从url构建database
```bash
python src/build_db.py --db-name {db_name} --file-path {file_path}
```
url提取采取嵌套提取，深度限制为3.
参数说明：
- `db_name`: 你的知识库名称
- `file_path`: 存放你需要提取的url目录,项目自带[cesium参考文档入口](./websites.txt)作为示例。

2. CLI交互
```bash
python src/flow.py
```
3. GUI交互
```bash
python src/gui.py
```

## 注意事项

1. 确保已安装所有必要的依赖包
2. 配置正确的 API 密钥和基础 URL
3. 注意爬取频率，避免对目标网站造成压力
4. 定期备份重要数据
5. 监控错误日志，及时处理异常情况

## 许可证

[MIT License](LICENSE)
