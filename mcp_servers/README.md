# MCP Servers

为 PM Agent 提供项目管理数据和知识库查询工具。

## 📚 服务列表

### Project Server (`project_server.py`)
**项目管理服务** - 端口 8003

**核心工具：**
- `list_all_projects` - 列出所有项目及状态
- `get_milestones` - 获取项目里程碑
- `analyze_risks` - 项目风险分析
- `calculate_health_score` - 计算项目健康度评分
- `list_blocked_tasks` - 列出阻塞任务
- `get_project_progress` - 获取项目整体进度

### Knowledge Server (`knowledge_server.py`)
**知识库服务** - 端口 8004

**核心工具：**
- `search_documents` - 搜索知识库文档
- `get_document_content` - 获取文档完整内容
- `list_meeting_notes` - 列出会议纪要
- `aggregate_report_data` - 聚合项目报告数据

## 🚀 快速开始

### 安装依赖
```bash
pip install fastmcp
```

### 启动服务

**方式一：使用 Makefile（推荐）**
```bash
make start   # 启动所有 MCP + FastAPI 服务
make stop    # 停止所有服务
```

**方式二：手动启动**
```bash
python mcp_servers/project_server.py
python mcp_servers/knowledge_server.py
```

## 💡 使用示例

### PM Agent 风险扫描

```
用户: 帮我评估当前项目的风险

Agent 自动执行:
1. list_all_projects() → 查看所有项目状态
2. analyze_risks("project-1") → 分析项目风险维度
3. calculate_health_score("project-1") → 计算健康度评分
4. search_documents("风险") → 查询历史风险记录
5. 综合分析 → 生成风险评估报告和建议
```

### 工具参数示例

**项目风险分析：**
```python
analyze_risks(
    project_id="project-1"
)
# 返回: 技术风险、资源风险、进度风险等维度的详细分析
```

**搜索知识库文档：**
```python
search_documents(
    query="周报模板",
    doc_type="report"
)
# 返回: 匹配的文档列表及摘要
```

**列出会议纪要：**
```python
list_meeting_notes(
    project_id="project-1",
    days=14
)
# 返回: 近两周的会议纪要列表
```

## 🔧 高级配置

### 接入真实 API

当前返回模拟数据。接入真实 API 步骤：

**项目管理工具集成：**
- Jira / Linear / Asana API
- Git 仓库集成（GitHub / GitLab）
- 飞书 / 钉钉 通知集成

**知识库集成：**
- 飞书文档 / Notion / Confluence API
- 本地文件系统监控
- 自动向量化索引

### 自定义 Mock 数据

修改各 Server 文件中的数据生成逻辑，模拟实际项目场景。

## 📚 参考资料

- [FastMCP 文档](https://github.com/jlowin/fastmcp)
- [MCP 协议](https://modelcontextprotocol.io/)
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [主项目 README](../README.md)

---

**注意**: 当前版本返回模拟数据，生产环境需配置真实 API。
