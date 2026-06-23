> ⚠️ **MOCK 数据 — 仅供 PM AI Agent 演示使用，非真实项目文档**

# 大模型对话模块技术方案 v1.0（示例）

## 技术选型

### 核心技术栈
- **LLM层**: DeepSeek API（OpenAI兼容模式）
- **Agent框架**: LangChain + LangGraph
- **向量检索**: Milvus（IVF_FLAT索引，L2距离）
- **工具协议**: MCP（Model Context Protocol）
- **Web框架**: FastAPI + SSE流式输出

### 架构设计

```
用户请求 → FastAPI → Dispatch Agent
                      ├─ 对话Agent → Milvus RAG检索
                      ├─ 项目Agent → Plan-Execute-Replan
                      └─ 知识Agent → 文档向量搜索
```

## 模块设计

### 对话管理Agent
- 基于LangGraph StateGraph实现多轮对话
- MemorySaver实现会话状态持久化
- 支持消息历史修剪（最近7条）

### 知识检索Agent
- 文档上传 → Markdown分割 → 向量嵌入 → Milvus存储
- 查询 → 向量搜索 → Top-K召回 → 上下文整合

### 工具调用机制
- 通过MCP协议封装外部工具
- MultiServerMCPClient管理多服务器连接
- 指数退避重试机制（最多3次）

## 性能指标
- 单次API调用 < 3s
- 向量搜索 < 100ms
- 并发用户 ≥ 500
