# 活动上下文 (Active Context)

## 2025-04-05: 初始化文档

- 创建了`doc/productContext.md`文件，详细说明项目目的、解决的问题和工作方式
- 创建了`doc/systemPatterns.md`文件，记录系统架构模式
- 创建了`doc/activeContext.md`文件，用于记录项目修改历史
- 创建了`.cursorRule`文件，记录项目关键信息
- 确保文档与现有README.md保持一致
- 分析了项目的整体结构和主要功能点
- 完善了系统架构模式的文档，包括节点链模式、配置注入模式等

## 2025-04-05: 更新nodes.md文档

- 更新了`doc/nodes.md`文件，使其与当前代码实现保持同步
- 修正了LLMNode的配置参数和输入输出格式，包括默认模型名称和温度参数
- 调整了APIQueryNode的输出格式，添加了answer和request_id字段
- 更新了EmbeddingNode的配置参数，将模型名称更新为text-embedding-3-small
- 修正了VectorDBNode的配置参数和处理逻辑说明
- 简化了各节点的输入输出格式，移除了status和message字段，符合当前实现
- 更新了节点间数据传递的详细信息 

## 2025-05-04: 扩展default模型配置

- 在`configs/config.json`中添加了多个默认模型配置
- 添加了GPT系列模型（gpt-3.5-turbo、gpt-4.5-preview等）
- 添加了OpenAI最新的O系列模型（o1-mini、o1-preview、o3-mini、o1）
- 添加了gpt-4o和gpt-4o-mini模型配置
- 添加了Claude模型配置（claude-3-7-sonnet、claude-3-5-sonnet）
- 添加了Gemini模型配置（gemini-1.5-pro、gemini-1.5-flash）
- 添加了DeepSeek和Grok模型配置
- 所有新增配置保持与原default_gpt_4一致的结构 