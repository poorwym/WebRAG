# Nodes 文档

本文档详细介绍了系统中各个节点的功能、输入和输出。

## 基础节点 (Node)

所有节点的基类，定义了基本的节点接口。

### 输入
```python
{
    "node_id": str,  # 节点的唯一标识符
    "config": dict   # 节点的配置字典（可选）
}
```

### 输出
```python
{
    "status": str,   # 处理状态（"success" 或 "error"）
    "message": str,  # 状态信息
    "data": dict     # 处理结果数据
}
```

### 方法
- `process(data: dict) -> dict`: 抽象方法，所有子类必须实现
- `print_config()`: 打印节点配置信息
- `print_node_id()`: 打印节点ID

## LLM节点 (LLMNode)

用于调用大语言模型生成回答的节点。

### 配置参数
```python
{
    "model": str,             # 模型名称（默认：gpt-4-turbo-preview）
    "temperature": float,     # 温度参数（默认：0.7）
    "base_url": str,          # API基础URL（默认：https://api.chatanywhere.tech/v1）
    "prompt_template": str    # 自定义提示词模板（默认：{user_query}）
}
```

### Prompt模板
LLM节点支持自定义提示词模板，模板中可以使用以下变量：
- `{context}`: 上下文信息
- `{user_query}`: 用户问题

### 输入
```python
{
    "context": str,        # 上下文信息
    "user_query": str      # 用户问题
}
```

### 输出
```python
{
    "answer": str,         # LLM生成的回答
    "request_id": str      # 请求ID（基于时间戳生成）
}
```

## API查询节点 (APIQueryNode)

用于分析用户查询中可能涉及的Cesium API的节点，继承自LLMNode。

### 配置参数
- 继承LLMNode的所有配置参数
- 自动设置专门用于API查询的提示词模板（覆盖LLMNode的模板）

### Prompt模板
默认模板如下：
```
请分析以下用户查询中可能涉及到的 Cesium API，并用简短的陈述句表达出来，不同api间用逗号间隔。
只关注 API 相关的部分，不需要其他解释。
如果查询中没有明确的 API 相关描述，请返回"无明确的 API 相关描述"。

用户查询:
{user_query}

请用陈述句表达:
```

### 输入
```python
{
    "user_query": str           # 用户的查询
}
```

### 输出
```python
{
    "api_description": str,     # 分析出的API描述
    "answer": str,              # 与api_description相同，保持与LLMNode输出一致
    "request_id": str           # 请求ID（基于时间戳生成）
}
```

## Embedding节点 (EmbeddingNode)

用于将文本转换为向量表示的节点。

### 配置参数
```python
{
    "model": str,             # 模型名称（默认：text-embedding-3-small）
    "base_url": str           # API基础URL（默认：https://api.chatanywhere.tech/v1）
}
```

### 输入
```python
{
    "api_description": str    # 需要转换为向量的API描述
}
```

### 输出
```python
{
    "embeddings": list,       # API描述的向量表示列表
    "api_description": str    # 原始API描述
}
```

## 向量数据库节点 (VectorDBNode)

用于在向量数据库中检索相似文档的节点。

### 配置参数
```python
{
    "persist_directory": str,  # 向量数据库持久化目录路径
    "model": str               # embedding模型名称（用于定位正确的向量数据库目录）
}
```

### 输入
```python
{
    "embeddings": list        # 查询向量列表
}
```

### 输出
```python
{
    "retrieved_docs": list    # 检索到的文档列表（每个向量检索k=3条文档）
}
```

## 检索器节点 (RetrieverNode)

用于处理和格式化检索到的文档的节点。

### 输入
```python
{
    "retrieved_docs": list    # 检索到的文档列表
}
```

### 输出
```python
{
    "context": str            # 处理后的文档内容（将所有文档内容合并为字符串）
}
```

## 输出节点 (OutputNode)

用于最终输出处理的节点。

### 输入
```python
{
    "input": str              # 输入文本（通常是LLM生成的回答）
}
```

### 输出
```python
{
    "final_output": str       # 格式化后的最终输出
}
```

## 节点流程示例

一个典型的查询流程如下：

1. 用户输入查询
2. APIQueryNode分析查询中涉及的Cesium API
3. EmbeddingNode将API描述转换为向量
4. VectorDBNode使用向量检索相关文档
5. RetrieverNode处理和格式化检索到的文档
6. LLMNode基于文档生成回答
7. OutputNode格式化并输出最终结果 