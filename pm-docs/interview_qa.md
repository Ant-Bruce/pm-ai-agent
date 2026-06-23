# PM AI Agent 面试问答手册

---

## 一、项目概述

### Q: 请简单介绍一下这个项目

**答**：PM AI Agent 是一个智能项目管理助手，解决多项目并行管理中的风险滞后、信息分散、报告重复劳动三大痛点。

核心能力：
- 🔍 **风险扫描**：自动扫描所有活跃项目，分析进度/资源/技术三维风险，输出红黄绿分级报告
- 📊 **健康度评估**：从进度(35%)、质量(25%)、资源(25%)、风险(15%)四维度量化打分
- 📝 **日报/周报生成**：自动聚合项目数据，生成结构化 Markdown 报告
- 📄 **文档语义问答**：基于 PRD、技术方案、会议纪要的 RAG 检索增强问答

技术栈：FastAPI + LangChain/LangGraph + Milvus 向量库 + MCP 协议 + DeepSeek LLM

架构亮点：多 Agent 协同（对话Agent / 项目Agent / 知识Agent），通过 Dispatch Agent 自动识别意图并路由。

---

### Q: 为什么要做多 Agent 架构？单 Agent 不行吗？

**答**：单 Agent 有明确的局限性。项目管理场景有 4 种完全不同的任务类型：

| 任务类型 | 需要的处理方式 | 为什么单Agent不行 |
|---------|-------------|----------------|
| 风险扫描 | 多步推理、链式工具调用 | 需要 Plan-Execute-Replan 循环，单Agent容易遗漏步骤 |
| 文档问答 | 向量检索 + 上下文整合 | 需要专门的 RAG 管道，单Agent无法高效处理 |
| 周报生成 | 模板驱动 + 多源数据聚合 | 需要聚合6-8个工具的数据，单Agent容易超上下文 |
| 闲聊/帮助 | 快速简单响应 | 不需要复杂推理，单Agent过度调用工具 |

多 Agent 的优势：
1. **专用化**：每个 Agent 有独立的 system prompt 和工具集，更精准
2. **可扩展**：新增场景只需新增 Agent，不影响现有能力
3. **可观测**：每个 Agent 的执行链路独立，方便调试和优化

---

### Q: Dispatch Agent 是怎么做意图识别的？

**答**：我用的是 LLM + Structured Output 的方案，不是关键词匹配。

流程：
1. 用户输入 → 进入 Dispatch Prompt（描述了4种Agent的职责和关键词）
2. LLM 返回结构化 JSON：`{"agent_type": "project_agent", "confidence": 0.95, "reasoning": "..."}`
3. 根据 agent_type 路由：`project_agent` → Plan-Execute-Replan / `knowledge_agent` → RAG / `report_agent` → Plan-Execute / `chat_agent` → 对话

为什么不用关键词匹配？
- 用户表达多样："帮我看看项目有没有问题" ≠ "风险扫描"，但意图相同
- LLM 能理解语义，覆盖边缘场景。关键词匹配需要穷举所有说法，维护成本高

备选方案对比：
- 关键词匹配：快但不够准，适合 MVP
- Embedding 相似度分类：需要标注数据，冷启动困难
- LLM 判断：零样本可用，准确率最好（实测 >95%），就是多一次 API 调用（~0.5s）

---

## 二、RAG 知识库

### Q: 知识库是怎么做的？长文档怎么处理？

**答**：三段式分割 + 结构化元数据保留。

```
上传文档 → 先删旧数据 → 三阶段分割 → 批量向量化 → 存入 Milvus
```

**三阶段分割策略**：
1. **标题结构切分**（MarkdownHeaderTextSplitter）：按 `#`(h1) 和 `##`(h2) 切分，不按 `###` 切（防碎片化）
2. **长度二次切分**（RecursiveCharacterTextSplitter）：chunk_size=1600字，overlap=100字，保证上下文连续
3. **小片段合并**：<300字的片段合并到相邻片段（不超过1600字），避免"孤岛信息"

**为什么这样设计？**
- 纯粹按长度切：会切断语义边界，如"PRD的里程碑表格"被切成两半
- 纯粹按标题切：某些章节太长（如技术方案正文），embedding 质量下降
- 三段式方案：标题保持语义完整 + 长度控制不超限 + 合并防止碎片

**元数据保留**：每个 chunk 保留来源文件、h1/h2 标题层级，检索时可以定位到具体章节。

**配置参数**：
- `CHUNK_MAX_SIZE=800` → 二阶段实际用 1600字
- `CHUNK_OVERLAP=100` → 片段间重叠，防止跨边界信息丢失
- `RAG_TOP_K=3` → 每次检索返回 3 个最相关片段

**向量化**：SiliconFlow 的 Qwen3-Embedding-8B（1024维），当前版本 MTEB 中文排名前3。

---

### Q: 检索结果不好怎么办？怎么优化？

**答**：优化 RAG 检索质量有四个方向：

1. **切分策略调优**：
   - 当前 chunk_size=1600 适合中文技术文档
   - 如果检索内容太碎 → 增大 chunk_size（如 2000-2400）
   - 如果检索不够精准 → 减小 chunk_size（如 800-1000）

2. **检索策略增强**：
   - 当前用 Top-K 召回（k=3），可改为 Top-K + 阈值过滤（相似度 < 0.7 的丢弃）
   - 可加 Reranker 模型做二次排序（如 BGE-Reranker）
   - 可混合检索：向量检索 + BM25 关键词检索（Hybrid Search）

3. **查询优化**：
   - HyDE（Hypothetical Document Embeddings）：先让 LLM 生成假设答案，用假设答案做检索
   - Query Rewriting：用 LLM 把用户问题改写为更精准的检索查询

4. **知识库质量**：
   - 确保文档结构化（有清晰标题层级）
   - 删除冗余/过时文档
   - 同一主题有多个角度文档时，检索效果更好

---

### Q: Embedding 为什么用 Qwen3-Embedding-8B 而不是 OpenAI 的？

**答**：选型考量：

| 维度 | Qwen3-Embedding-8B（via SiliconFlow） | OpenAI text-embedding-3 |
|------|--------------------------------------|------------------------|
| 成本 | 免费额度/极低价格 | $0.02/1M tokens |
| 中文能力 | MTEB 中文榜 top3 | 中等（英文为主） |
| 维度 | 支持自定义 256-4096 | 支持 256/1024/3072 |
| 调用方式 | 标准 OpenAI API 兼容 | 标准 OpenAI API |

选它的核心原因：**中文技术文档的语义理解更好**。比如"需求评审"和"PRD审核"这种同义表达，Qwen3 比 OpenAI 的召回率高 10-15%。

### Q: 知识库怎么保证文档质量？脏数据怎么办？

**答**：从四个环节保障知识质量：

**① 文档准入机制**
- 上传时校验文件类型（只允许 .md / .txt），过滤二进制、图片等不可索引文件
- 限制单文件大小（10MB），防止超大文件撑爆向量库
- 文件名清洗：过滤特殊字符，防止路径注入

**② 文档更新机制（去重 + 覆盖）**
```python
# 上传新文档时的处理流程
vector_store_manager.delete_by_source(file_path)  # 1. 先删旧数据
documents = splitter.split_document(content)        # 2. 重新切分
vector_store_manager.add_documents(documents)       # 3. 写入新数据
```
同一个文件再次上传时，先删除该文件的所有旧 chunks，再写入新的。保证向量库里同一个文件不会出现两份不同版本的数据。

**③ 检索层质量控制**
- **Top-K 召回**：默认 k=3，避免无关内容污染上下文
- **相似度阈值**：可配置最低相似度过滤（当前用 L2 距离，draft 中可切换为 COSINE + 阈值）
- **元数据过滤**：按文件来源、文档类型（prd/tech_spec/meeting）、时间范围做前置过滤
- **结构化元数据保留**：每个 chunk 保留 h1/h2 标题层级，检索结果带章节信息，用户知道这段内容来自哪里

**④ 可做但还没做的（生产级）**
| 手段 | 说明 |
|------|------|
| 文档审核流程 | 上传后需 PM 审核通过才入库，防止错误文档污染 |
| 时效性管理 | 过时文档自动降权或归档（如半年前的会议纪要权重减半） |
| 质量评分 | 根据文档被检索后用户是否采纳，给文档打分 |
| 人工反馈闭环 | 用户标记"此答案不对"，关联的 chunks 权重降低 |
| 重复文档检测 | 上传时计算文档相似度，提醒"已有类似文档，确认覆盖？" |

**核心思路**：准入 → 去重覆盖 → 检索过滤 → 人工反馈，形成知识质量闭环。面试时可以说："当前实现了前两层保障，生产环境需要补齐审核和反馈机制。"

---

## 三、MCP 工具协议

### Q: MCP 是什么？为什么要用？

**答**：MCP（Model Context Protocol）是 Anthropic 提出的 AI 工具集成标准协议。

**核心概念**：
- MCP Server：提供工具的服务端（如 "ProjectManager" 提供 `list_all_projects`）
- MCP Client：调用工具的客户端（Agent 通过 Client 调用 Server 的工具）
- Transport 层：支持 stdio（本地进程）和 streamable-http（远程服务）

**为什么要用 MCP？**

传统做法：每个工具写一个 LangChain Tool 函数
```python
# 传统方式：工具和Agent强耦合
@tool
def list_projects(): ...
@tool
def analyze_risks(): ...
# ... 10个工具，全部写在Agent代码里
```

MCP 方式：工具独立部署，Agent 通过协议发现和调用
```
Agent → MCP Client → MCP Server(project:8003) → 6个工具
                   → MCP Server(knowledge:8004) → 4个工具
```

**优势**：
1. **解耦**：新增工具不需要改 Agent 代码，只需在 MCP Server 里加函数
2. **复用**：多个 Agent 可以共享同一套 MCP 工具
3. **标准化**：不同语言写的 Server 都可以被同一个 Client 调用
4. **独立部署**：MCP Server 独立运行、独立监控、独立扩缩容

---

### Q: 你的 MCP 工具怎么设计的？有什么模式？

**答**：我设计了 2 个 MCP Server，10 个工具，遵循以下设计模式：

**ProjectManager Server（6个工具，端口8003）**：
| 工具 | 职责 | 设计考量 |
|------|------|---------|
| `list_all_projects(status_filter)` | 获取项目列表 | 支持过滤，避免Agent获取过多无关数据 |
| `get_project_progress(project_id)` | 详细进度 | 返回燃尽图数据，Agent可据此做趋势分析 |
| `analyze_risks(project_id)` | 三维风险分析 | 返回 severity 字段，Agent用于分级标注 |
| `calculate_health_score(project_id)` | 四维评分 | 返回权重+分数，Agent可解释评分逻辑 |
| `list_blocked_tasks(project_id)` | 阻塞任务 | 返回阻塞原因和天数，Agent判断优先级 |
| `get_milestones(project_id)` | 里程碑 | 返回 planned vs actual 对比 |

**KnowledgeManager Server（4个工具，端口8004）**：
| 工具 | 职责 |
|------|------|
| `search_documents(query, doc_type)` | 多类型文档搜索 |
| `get_document_content(doc_id)` | 完整文档内容 |
| `list_meeting_notes(project_id, days)` | 会议纪要查询 |
| `aggregate_report_data(project_id, report_type)` | 周报数据聚合 |

**设计原则**：
1. **单一职责**：每个工具只做一件事，Agent组合使用
2. **参数可选**：支持默认值，降低Agent调用复杂度
3. **返回结构化**：JSON 格式，Agent能直接解析使用
4. **重试机制**：`retry_interceptor` 指数退避重试（最多3次），避免临时故障导致整个任务失败

---

## 四、Plan-Execute-Replan

### Q: 为什么选 Plan-Execute-Replan 而不是 ReAct？

**答**：两种模式的适用场景不同：

| 维度 | ReAct | Plan-Execute-Replan |
|------|-------|-------------------|
| 推理模式 | 思考→行动→观察 循环 | 先制定完整计划→逐步执行→评估调整 |
| 适合任务 | 简单查询（2-3步） | 复杂分析（4-10步） |
| 步骤依赖 | 每步独立 | 步骤间有依赖关系 |
| 透明度 | 用户看不到全局计划 | 用户一开始就看到完整计划 |
| Token消耗 | 低 | 中（多了计划制定步骤） |

**PM Agent 为什么选 Plan-Execute-Replan？**

项目管理分析需要 5-8 步工具调用（列出项目→查进度→分析风险→查阻塞→算健康度→生成报告），步骤间有明确依赖。ReAct 容易在中间步骤"迷路"，而 Plan-Execute 让 LLM 先全局规划再执行，每一步都清楚自己在干什么。

**示例对比**：
- ReAct 做风险扫描：第1步查项目→第2步查进度→第3步"咦我该查什么来着？再看看"→第4步查风险→...
- Plan-Execute：一开始生成6步计划→用户看到完整计划→逐步执行→每步完成标记✓→最终报告

---

### Q: Replanner 怎么防无限循环？

**答**：三层防护机制：

1. **硬上限**：`MAX_STEPS=8`，超过8步强制生成响应（不管数据是否完整）

2. **软限制**：已执行 ≥5 步时，禁止 `replan`（调整计划），只能 `continue` 或 `respond`

3. **决策优先级**（写进 prompt）：
   ```
   respond（足够好就结束）> continue（继续执行）> replan（调整计划）
   ```

4. **步骤守恒**：`replan` 时新步骤数 ≤ 当前剩余步骤数，防止计划膨胀

实测效果：在没有这些防护时，LLM 倾向于"再查一步看看"，容易跑 15+ 步。加了防护后，90% 的任务在 3-6 步内完成。

---

### Q: Planner 的结构化输出怎么做的？

**答**：用过两种方案：

**方案一（最初）**：`llm.with_structured_output(Plan)` — 让 LangChain 自动处理 JSON 结构化输出。问题：DeepSeek 对这个功能的兼容性不好，有时返回的 JSON 解析失败。

**方案二（当前）**：手动 JSON 解析。
```
Prompt → LLM 返回 JSON 文本 → 正则提取 ```json{...}``` → json.loads()
```
如果 JSON 解析失败 → 回退方案：按行解析"步骤N: ..." 格式
如果回退也失败 → 兜底：返回默认 3 步计划

**经验**：不同 LLM 对 structured output 支持差异大，手写健壮解析器比依赖框架更靠谱。

---

## 五、架构设计

### Q: 这个系统的整体架构是什么样的？

**答**：

```
浏览器（Static HTML/CSS/JS）
    │  SSE / REST
    ▼
FastAPI (app/main.py)  ← 路由分发
    ├─ /api/chat        → RagAgentService（对话Agent）
    ├─ /api/pm          → PMService（编排层）
    │   ├─ Dispatch     → 意图识别
    │   ├─ PlanExecute  → Planner → Executor → Replanner
    │   └─ RAG/KB       → 知识库检索
    ├─ /api/upload      → 文档向量化入库
    └─ /health          → 健康检查
    │
    ▼
LLM Layer：DeepSeek API (deepseek-chat)
    │
    ▼
MCP Layer：
    ├─ ProjectManager Server (port 8003)  → 6工具
    └─ KnowledgeManager Server (port 8004) → 4工具
    │
    ▼
Vector Layer：
    ├─ SiliconFlow Qwen3-Embedding-8B（1024维）
    └─ Milvus Vector Store (Docker, IVF_FLAT)
```

**数据流示例（风险扫描）**：
```
用户点击「风险扫描」
  → POST /api/pm {task_type:"risk_scan"}
  → PMService.handle_request()
  → PlanExecute Agent
    → Planner: 查询知识库 → 获取工具列表 → 生成6步计划
    → Executor: pop步骤 → llm.bind_tools → ToolNode调用 → 返回结果
    → Replanner: 评估 → continue
    → Executor: 下一步...
    → Replanner: respond → 生成最终报告
  → SSE 流式返回 {plan, step_complete, status, report, complete}
  → 前端实时渲染 Markdown
```

---

### Q: 系统的性能瓶颈在哪？怎么优化？

**答**：

| 瓶颈 | 影响 | 优化方案 |
|------|------|---------|
| LLM 调用延迟 | 每次 1-3s，整个风险扫描 30-50s | 1. 换成更快模型（DeepSeek-V3→更小模型做简单任务）2. 并行调用（Plan阶段同时查知识库+工具列表） |
| 多次 LLM 调用 | Planner→每个Executor→每个Replanner 都是独立调用 | 1. Plan用便宜的模型，Report用强模型 2. 中间步骤结果短时缓存 |
| MCP 工具调用 | 网络往返+重试 | 1. 预取常用数据 2. 增加本地工具减少MCP调用 |
| 向量检索 | embedding 生成+Milvus搜索 | 1. GPU embedding加速 2. 索引优化（HNSW替代IVF_FLAT） |
| 文档上传 | 同步等待embedding完成 | 1. 异步队列处理 2. 批量上传优化 |

**当前实际数字**：风险扫描 ~45秒（6步）、周报生成 ~60秒（9步）。生产环境可优化至 20-30秒。

---

## 六、项目难点与收获

### Q: 这个项目最大的技术难点是什么？

**答**：三个难点：

1. **多工具协同的可靠性**
   - 10 个 MCP 工具分布在 2 个独立服务上，任何一个挂掉都会影响 Agent 执行
   - 解决：`retry_interceptor` 指数退避重试 + 工具失败后 Agent 继续执行（不崩溃）+ 报告中如实标注"此步骤失败"

2. **结构化输出的跨模型兼容**
   - 不同 LLM（MiniMax / DeepSeek / Qwen）对 JSON structured output 支持差异大
   - 解决：放弃框架的 `with_structured_output`，手写健壮 JSON 解析 + 多级回退方案

3. **Plan-Execute-Replan 的终止控制**
   - LLM 天然倾向于"再查一个工具看看"，容易无限循环
   - 解决：三层防护（硬上限8步 + 软限制5步 + 决策优先级prompt引导）

---

### Q: 如果重新做，你会怎么改进？

**答**：

1. **加 Streaming 中间状态**：当前只有步骤完成才推送事件，中间 LLM 思考过程对用户是黑盒。应该实时显示"正在查询项目列表..."、"正在分析风险..."

2. **引入 Human-in-the-Loop**：关键决策（如风险等级判断、周报关键结论）让用户确认后再继续，提升准确性

3. **工具结果缓存**：同一个项目一天内多次查询，应该缓存 MCP 返回结果，减少重复调用

4. **评估数据集**：建立项目管理领域的 Agent 评估基准，量化衡量计划准确度、工具选择合理度、报告质量

5. **前端交互优化**：当前是纯文本流式输出，理想状态是结构化卡片（风险卡片、进度仪表盘、燃尽图）实时更新

---

## 七、面试常问补充

### Q: 为什么用 Milvus 而不是其他向量数据库？

- Milvus：成熟的分布式向量库，支持十亿级向量，社区活跃。适合生产环境
- Chroma：轻量，适合原型验证。但分布式能力弱
- Pinecone：全托管，省运维。但数据在云端，内网场景不行
- 选 Milvus 的原因：内网可部署 + Docker一键启动 + 支持多种索引 + LangChain 官方集成

### Q: 怎么保证 Agent 调用的安全性？

1. MCP 工具层：返回数据都是 mock，生产环境需要加权限校验
2. LLM 层：system prompt 限定 Agent 只做项目管理任务，防止 prompt injection
3. 前端：文件上传限制类型(.txt/.md)和大小(10MB)
4. CORS：只有开发环境 allow all，生产需限制域名

### Q: 这个系统能支撑多少并发？

- FastAPI 异步框架：理论支持 1000+ 并发连接
- 实际瓶颈在 LLM API：DeepSeek 有 RPM（每分钟请求数）限制
- 推荐使用场景：5-10 个 PM 同时使用，每个请求处理 30-60秒
- 生产优化方向：加请求队列 + LLM调用限流 + 结果缓存
