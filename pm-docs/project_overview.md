# PM AI Agent — 项目速览

## 一句话描述
基于 LangChain/LangGraph 的多 Agent 智能项目管理助手，支持风险扫描、健康度评估、周报生成和文档语义问答。

## 技术栈速查
| 层 | 技术 | 说明 |
|---|------|------|
| 框架 | FastAPI + LangChain + LangGraph | Web + Agent 编排 |
| LLM | DeepSeek (deepseek-chat) | OpenAI 兼容模式 |
| 向量库 | Milvus (Docker, 1024维) | IVF_FLAT 索引 |
| Embedding | Qwen3-Embedding-8B (SiliconFlow) | 中文 SOTA |
| 工具协议 | MCP (Model Context Protocol) | 2 Server, 10 工具 |
| 前端 | Vanilla HTML/CSS/JS | 无框架依赖 |
| 部署 | Docker Compose (Milvus) + Python | 一键启动 |

## 架构图（文字版）
```
用户 → FastAPI → Dispatch Agent → {
  project_agent: Planner → Executor → Replanner (Plan-Execute-Replan)
  knowledge_agent: RAG检索 → LLM生成 (文档问答)
  report_agent: 数据聚合 → 模板填充 (周报生成)
  chat_agent: 通用对话 (闲聊)
}
  ↓
MCP Client → ProjectManager(8003:6工具) + KnowledgeManager(8004:4工具)
  ↓
DeepSeek LLM + SiliconFlow Embedding + Milvus Vector DB
```

## 核心数字
- 多 Agent：4 个（对话/项目/知识/报告）
- MCP 工具：10 个（project 6 + knowledge 4）
- 知识库：5 份 PM 文档
- Plan-Execute-Replan：90% 任务 3-6 步完成
- 风险扫描全流程：~45s
- API：POST /api/pm 统一入口

## 关键设计决策
1. **Plan-Execute-Replan over ReAct**：复杂分析需要全局计划
2. **多 Agent over 单 Agent**：专用化和可观测性
3. **MCP over 硬编码工具**：解耦和复用
4. **手写JSON解析 over structured_output**：跨模型兼容
5. **暗色主题原版前端**：保持简单，核心是后端能力
