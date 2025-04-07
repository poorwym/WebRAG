# 系统架构模式 (System Patterns)

## 整体架构

CesiumRAG采用模块化的节点设计模式，每个节点负责特定功能，可独立配置和扩展。系统遵循以下架构模式：

## 核心模式

### 1. 节点链模式 (Node Chain Pattern)

系统采用链式处理流程，每个节点接收上一节点的输出作为输入，执行特定的处理逻辑，并将结果传递给下一节点：

```
用户输入 → APIQueryNode → EmbeddingNode → VectorDBNode → RetrieverNode → LLMNode → OutputNode → 最终输出
```

每个节点遵循统一的输入/输出接口，确保数据流的一致性。

### 2. 配置注入模式 (Configuration Injection)

节点通过配置字典初始化，支持灵活的配置注入：

```python
node = Node(node_id="my_node", config={"param1": "value1", "param2": "value2"})
```

配置可从外部JSON文件加载，便于系统参数调整而无需修改代码。

### 3. 向量检索模式 (Vector Retrieval Pattern)

采用"嵌入-检索-生成"的RAG架构：

1. **嵌入**：将查询转换为向量表示
2. **检索**：基于向量相似度检索相关文档
3. **生成**：将检索结果作为上下文，生成回答

### 4. 提示词模板模式 (Prompt Template Pattern)

LLM节点使用可配置的提示词模板，支持变量替换：

```
{template_with_variables} → 填充变量 → 完整提示词 → LLM
```

提示词模板可根据不同任务自定义，提高系统灵活性。

## 扩展模式

### 1. 插件式节点扩展 (Pluggable Node Extension)

系统支持通过继承基础节点类创建新的处理节点：

```python
class CustomNode(Node):
    def process(self, data):
        # 自定义处理逻辑
        return {"status": "success", "message": "处理完成", "data": result}
```

### 2. 预处理-后处理模式 (Pre/Post Processing)

节点可实现预处理和后处理钩子，在主要处理逻辑前后执行：

```python
def pre_process(self, data):
    # 数据预处理
    return processed_data

def post_process(self, result):
    # 结果后处理
    return processed_result
```

### 3. 异常处理包装模式 (Exception Handling Wrapper)

节点处理逻辑包含异常处理包装器，确保错误不会中断整个流程：

```python
try:
    # 核心处理逻辑
    result = process_data(data)
except Exception as e:
    # 异常处理
    return {"status": "error", "message": str(e), "data": {}}
```

## 界面模式

### 1. MVC模式 (Model-View-Controller)

GUI部分采用MVC架构：
- **Model**：节点链和处理逻辑
- **View**：PyQt5界面组件
- **Controller**：处理用户交互和更新视图

### 2. 异步处理模式 (Asynchronous Processing)

用户界面采用异步模式处理长时间运行的操作，防止UI阻塞：

```python
def process_query(self):
    self.worker = Worker(self.run_query)
    self.worker.signals.finished.connect(self.on_query_finished)
    self.threadpool.start(self.worker)
```

## 数据流模式

### 1. 数据传递模式 (Data Passing Pattern)

节点间通过字典传递数据，保持原始数据的同时添加新的处理结果：

```python
input_data = {"user_query": "查询内容"}
output_data = {"user_query": "查询内容", "new_field": "新数据"}
```

### 2. 数据持久化模式 (Data Persistence Pattern)

向量数据库采用持久化存储模式，支持增量更新和快速加载：

```python
db = chromadb.PersistentClient(path=persist_directory)
``` 