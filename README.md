# PM AI Agent

> 企业级智能项目管理助手，支持 RAG 知识库问答和多智能体协作

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-latest-orange.svg)](https://www.langchain.com/)

## 背景

在项目管理中，PM 每天要处理大量重复性工作：扫描项目风险、汇总周报、回答团队对文档的反复询问、评估项目健康度。这些任务虽然模式化，但每次都需要翻文档、查数据、手动整合，耗费大量时间。

PM AI Agent 的目标就是把这一套流程自动化。它不是一个简单的 Chatbot，而是一个**具备规划和执行能力的智能代理**：

1. **理解意图** — 你说的"看看项目有没有风险"和"帮我扫一下风险"它能识别为同一件事
2. **制定计划** — 把模糊需求（"生成周报"）拆成具体步骤：先查里程碑 → 再拉任务列表 → 汇总阻塞项 → 最后成文
3. **调用工具** — 通过 MCP 协议对接项目管理平台（Jira/飞书/...），实际拉取数据而非凭空编造
4. **自适应调整** — 某一步卡住了，自动换条路走，不会傻等也不会胡编

底层用了 LangGraph 的 Plan-Execute-Replan 模式，加上 RAG 让它可以"读懂"你的项目文档（PRD、技术方案、会议纪要），再通过 MCP 标准化工具接口打通外部数据源。三者组合起来，就是一个能真正干活的 PM 助手。

### 工作原理

```
用户输入（"扫描项目风险"）
        │
        ▼
  ┌─────────────┐
  │  Dispatch   │  意图识别 → 决定交给哪个 Agent
  └──────┬──────┘
         │
    ┌────┴────┬─────────┐
    ▼         ▼         ▼
Project    Report   Knowledge
 Agent      Agent     Agent
    │         │         │
    └────┬────┘         │
         ▼              ▼
  Plan-Execute-Replan   RAG 检索
  ┌─────────────────┐   ┌──────────┐
  │ Planner         │   │ Milvus   │
  │ 查询知识库+拆步骤 │   │ 向量搜索  │
  │      ↓          │   └────┬─────┘
  │ Executor        │        │
  │ LLM+工具调用执行  │        │
  │      ↓          │        │
  │ Replanner       │        │
  │ 评估→继续/调整/输出│        │
  └────────┬────────┘        │
           │                 │
           └─────┬───────────┘
                 ▼
          SSE 流式输出
        （计划→步骤→报告 实时可见）
```

> **三种 Agent 的分工**：Project Agent 处理风险扫描/健康度评估（需多步推理），Report Agent 生成周报/日报（模板驱动），Knowledge Agent 回答文档问题（RAG 检索）。Dispatch 自动判断该用哪个，也可以直接指定 `task_type`。

## ✨ 核心特性

- 🤖 **智能对话** - LangChain 多轮对话 + 流式输出
- 📚 **RAG 问答** - 向量检索增强，支持文档上传、自动建立向量索引、自动更新知识库
- 📋 **PM Agent** - Plan-Execute 模式的项目管理智能代理（风险扫描、周报生成、文档问答）
- 🌐 **Web 界面** - 现代化 UI，支持多种对话模式：快速问答/流式对话
- 🔌 **MCP 集成** - 项目管理工具和知识库数据接入

## 🛠️ 技术栈

- **框架**: FastAPI + LangChain + LangGraph
- **LLM**: OpenAI 兼容 API（支持 DeepSeek / MiniMax / DashScope）
- **向量库**: Milvus
- **工具协议**: MCP (Model Context Protocol)

## 🚀 快速开始

### 环境要求
- Python 3.10+
- LLM API Key（DeepSeek / MiniMax / DashScope 任选其一）

### 安装和启动

#### Linux/macOS 环境

```bash
# 1. 克隆项目
git clone <repository_url>
cd super_biz_agent_py

# 2. 安装依赖（推荐使用 uv）
# 方式 1: 使用 uv（推荐，更快）
pip install uv
uv venv
source .venv/bin/activate
uv pip install -e .

# 方式 2: 使用 pip
pip install -e .

# 3. 编辑配置文件
# 首次使用需要编辑 .env 文件，填入你的 API Key
cp .env.example .env
vim .env  # 或使用其他编辑器

# 4. 一键初始化（启动 Docker + 服务 + 上传文档）
make init

# 5. 一键启动
make start
```

#### Windows 环境（PowerShell/CMD）

如果Windows 不支持 `make` 命令，可以手动执行以下步骤以启动服务：

```powershell
# 1. 克隆项目
git clone <repository_url>
cd super_biz_agent_py

# 2. 创建虚拟环境并安装依赖
# 方式 1: 使用 uv（推荐，更快）
pip install uv
# 创建虚拟环境
uv venv
# 激活虚拟环境
.venv\Scripts\activate
# 安装所有依赖
uv pip install -e .

# 方式 2: 使用 pip
python -m venv .venv
.venv\Scripts\activate
pip install -e .

# 3. 编辑配置文件
# 复制模板并编辑
copy .env.example .env
notepad .env

# 4. 启动 Docker Desktop
# 确保 Docker Desktop 已安装并正在运行

# 5. 启动 Milvus 向量数据库（Docker Compose）
docker compose -f vector-database.yml up -d

# 6. 等待 Milvus 启动完成（约 5-10 秒）
timeout /t 10

# 7. 启动 MCP 服务
# 启动 Project MCP 服务（新开一个 PowerShell 窗口）
python mcp_servers/project_server.py

# 启动 Knowledge MCP 服务（新开一个 PowerShell 窗口）
python mcp_servers/knowledge_server.py

# 8. 启动 FastAPI 主服务（新开一个 PowerShell 窗口）
# 注意：日志会自动输出到 logs\app_YYYY-MM-DD.log
python -m uvicorn app.main:app --host 0.0.0.0 --port 9900

# 9. 上传文档到向量库（新开一个 PowerShell 窗口）
# 等待服务启动完成后执行
timeout /t 5
python -c "import requests, os, time; [requests.post('http://localhost:9900/api/upload', files={'file': open(f'pm-docs/{f}', 'rb')}) or time.sleep(1) for f in os.listdir('pm-docs') if f.endswith('.md')]"
```

**Windows 一键启动脚本**（推荐）

使用启动脚本：

```powershell
# 启动所有服务
.\start-windows.bat

# 停止所有服务
.\stop-windows.bat
```

### 访问服务
- **Web 界面**: http://localhost:9900
- **API 文档**: http://localhost:9900/docs

## 📡 API 接口

### 核心接口

| 功能 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 普通对话 | POST | `/api/chat` | 一次性返回 |
| 流式对话 | POST | `/api/chat_stream` | SSE 流式输出 |
| PM Agent | POST | `/api/pm` | 项目管理代理（流式） |
| 文件上传 | POST | `/api/upload` | 上传并索引文档 |
| 健康检查 | GET | `/api/health` | 服务状态检查 |

### 使用示例

```bash
# 普通对话
curl -X POST "http://localhost:9900/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"Id":"session-123","Question":"你好"}'

# 流式对话
curl -X POST "http://localhost:9900/api/chat_stream" \
  -H "Content-Type: application/json" \
  -d '{"Id":"session-123","Question":"你好"}' \
  --no-buffer

# PM Agent
curl -X POST "http://localhost:9900/api/pm" \
  -H "Content-Type: application/json" \
  -d '{"session_id":"session-123","task_type":"risk_scan"}' \
  --no-buffer
```

## 📁 项目结构

```
super_biz_agent_py/
├── app/                                    # 应用核心
│   ├── __init__.py                         # 包初始化（自动加载日志配置）
│   ├── main.py                             # FastAPI 应用入口
│   ├── config.py                           # 配置管理（环境变量、MCP 服务器配置）
│   ├── api/                                # API 路由层
│   │   ├── __init__.py
│   │   ├── chat.py                         # 对话接口（RAG 聊天）
│   │   ├── pm.py                           # PM 接口（项目管理代理）
│   │   ├── file.py                         # 文件管理（文档上传）
│   │   └── health.py                       # 健康检查（服务状态）
│   ├── services/                           # 业务服务层
│   │   ├── __init__.py
│   │   ├── rag_agent_service.py            # RAG Agent（LangGraph 状态图）
│   │   ├── pm_service.py                   # PM 服务（计划-执行）
│   │   ├── vector_store_manager.py         # 向量存储管理器
│   │   ├── vector_embedding_service.py     # 向量embedding服务
│   │   ├── vector_index_service.py         # 向量索引服务
│   │   └── document_splitter_service.py    # 文档分割服务
│   ├── agent/                              # Agent 模块
│   │   ├── __init__.py
│   │   ├── mcp_client.py                   # MCP 客户端（工具调用）
│   │   ├── tools_registry.py               # 工具注册表
│   │   ├── pm/                             # PM Agent 核心逻辑
│   │   │   ├── __init__.py
│   │   │   ├── planner.py                  # 计划制定器
│   │   │   ├── replanner.py                # 重规划器
│   │   │   └── dispatch.py                 # 意图识别与分发
│   │   └── shared/                         # 共享模块
│   │       ├── __init__.py
│   │       ├── executor.py                 # 步骤执行器
│   │       ├── state.py                    # 状态定义
│   │       └── utils.py                    # 通用工具函数
│   ├── models/                             # 数据模型层
│   │   ├── __init__.py
│   │   ├── pm.py                           # PM 模型
│   │   ├── document.py                     # 文档模型
│   │   ├── request.py                      # 请求模型
│   │   └── response.py                     # 响应模型
│   ├── tools/                              # Agent 工具集
│   │   ├── __init__.py
│   │   ├── knowledge_tool.py               # 知识库查询工具
│   │   └── time_tool.py                    # 时间工具
│   ├── core/                               # 核心组件
│   │   ├── __init__.py
│   │   ├── llm_factory.py                  # LLM 工厂（模型管理）
│   │   └── milvus_client.py                # Milvus 客户端
│   └── utils/                              # 工具类
│       ├── __init__.py
│       └── logger.py                       # 日志配置（Loguru）
├── static/                                 # Web 前端（纯静态）
│   ├── index.html                          # 主页面
│   ├── app.js                              # 前端逻辑
│   └── styles.css                          # 样式表
├── mcp_servers/                            # MCP 服务器
│   ├── project_server.py                   # 项目管理服务
│   ├── knowledge_server.py                 # 知识库查询服务
│   └── README.md                           # MCP 服务说明
├── pm-docs/                                # 项目管理知识库（Markdown 文档）
├── logs/                                   # 日志目录（Loguru 自动创建）
│   └── app_YYYY-MM-DD.log                  # 按天轮转的日志文件
├── uploads/                                # 上传文件临时目录
├── volumes/                                # Milvus 数据持久化目录
├── .env.example                            # 环境变量配置模板
├── Makefile                                # 项目管理命令（Linux/macOS）
├── start-windows.bat                       # Windows 启动脚本
├── stop-windows.bat                        # Windows 停止脚本
├── vector-database.yml                     # Milvus Docker Compose 配置
├── pyproject.toml                          # 项目配置（依赖、元数据）
├── uv.lock                                 # uv 依赖锁定文件
├── pyrightconfig.json                      # Pyright 类型检查配置
└── README.md                               # 项目说明
```

## ⚙️ 配置说明

通过 `.env` 文件配置（参考 `.env.example`）：

```bash
# LLM 配置（OpenAI 兼容模式，支持 DeepSeek / MiniMax / DashScope）
DASHSCOPE_API_KEY=your-api-key
DASHSCOPE_API_BASE=https://api.deepseek.com
DASHSCOPE_MODEL=deepseek-chat

# SiliconFlow Embedding 配置
SILICONFLOW_API_KEY=your-siliconflow-key
SILICONFLOW_EMBEDDING_MODEL=Qwen/Qwen3-Embedding-8B

# Milvus 配置
MILVUS_HOST=localhost
MILVUS_PORT=19530

# RAG 配置
RAG_TOP_K=3
CHUNK_MAX_SIZE=800
CHUNK_OVERLAP=100
```

## 📋 PM Agent 智能项目管理

基于 **Plan-Execute-Replan** 模式实现的项目管理智能代理。

### 核心功能
- ✅ 自动制定执行计划（Planner）
- ✅ 智能工具调用（Executor）
- ✅ 动态调整步骤（Replanner）
- ✅ 流式输出分析过程
- ✅ 生成结构化报告

### 快捷操作

点击 Web 界面右上角的快捷按钮：
- 🔴 **风险扫描** - 分析项目风险并生成评估报告
- 🔵 **周报生成** - 自动汇总项目进展生成周报
- 🟢 **文档问答** - 基于知识库的智能问答

## 📝 开发指南

### 常用命令

```bash
# 项目管理
make init              # 一键初始化（Docker + 服务 + 文档）
make start             # 启动所有服务
make stop              # 停止所有服务
make restart           # 重启所有服务

# 依赖管理
make install-dev       # 安装开发依赖
make sync              # 同步依赖

# Docker 管理
make up                # 启动 Docker 容器
make down              # 停止 Docker 容器

# 代码质量
make format            # 格式化代码
make lint              # 代码检查
```

## 🐛 常见问题

### Windows 环境问题

#### 1. `make` 命令不可用
Windows 不支持 `make` 命令，请使用提供的批处理脚本：
```powershell
# 启动服务
.\start-windows.bat

# 停止服务
.\stop-windows.bat
```

#### 2. PowerShell 执行策略限制
如果遇到 "无法加载文件，因为在此系统上禁止运行脚本" 错误：
```powershell
# 临时允许脚本执行（管理员权限）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# 或者使用 CMD 而不是 PowerShell
cmd
.\start-windows.bat
```

#### 3. 端口被占用（Windows）
```powershell
# 查看占用端口的进程
netstat -ano | findstr :9900

# 结束进程（替换 PID 为实际进程 ID）
taskkill /F /PID <PID>
```

### 通用问题

### API Key 错误
```bash
# 检查环境变量
cat .env | grep API_KEY    # Linux/macOS
type .env | findstr API_KEY  # Windows
```

### Milvus 连接失败
```bash
# 确保本机有 Docker 服务并且已经启动（可以使用 Docker Desktop）

# 检查 Milvus 状态
docker ps | grep milvus

# 重启 Milvus（使用 docker compose）
docker compose -f vector-database.yml restart

# 或者重启单个服务
docker compose -f vector-database.yml restart standalone
```

### 服务无法启动

**Linux/macOS:**
```bash
# 查看服务日志
tail -f logs/app_$(date +%Y-%m-%d).log  # FastAPI 主服务（Loguru 日志）
tail -f mcp_knowledge.log                # Knowledge MCP 服务
tail -f mcp_project.log                  # Project MCP 服务

# 检查端口占用
lsof -i :9900  # FastAPI
lsof -i :8003  # Project MCP
lsof -i :8004  # Knowledge MCP
```

**Windows:**
```powershell
# 查看服务日志（获取今天的日期）
$today = Get-Date -Format "yyyy-MM-dd"
type logs\app_$today.log  # FastAPI 主服务（Loguru 日志）
type mcp_knowledge.log     # Knowledge MCP 服务
type mcp_project.log       # Project MCP 服务

# 或者查看最新的日志文件
Get-ChildItem logs\*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content -Tail 50

# 检查端口占用
netstat -ano | findstr :9900  # FastAPI
netstat -ano | findstr :8003  # Project MCP
netstat -ano | findstr :8004  # Knowledge MCP
```

## 📚 参考资源

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [LangChain 文档](https://python.langchain.com/)
- [LangGraph Plan-Execute](https://langchain-ai.github.io/langgraph/tutorials/plan-and-execute/)
- [MCP 协议](https://modelcontextprotocol.io/)

## 📄 许可证
MIT License
