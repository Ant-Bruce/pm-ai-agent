"""
PM Knowledge Server - 知识管理 MCP 服务（MOCK 数据）
提供文档搜索、会议纪要查询、报告数据聚合等工具
所有数据均为模拟数据，仅供演示使用
端口: 8004
"""

import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from fastmcp import FastMCP
from loguru import logger

mcp = FastMCP("KnowledgeManager")

# ============================================================
# Mock 文档数据
# ============================================================

MOCK_DOCUMENTS = [
    {
        "doc_id": "doc-001",
        "title": "智能客服系统升级 PRD v2.1",
        "type": "prd",
        "project": "智能客服系统升级",
        "project_id": "proj-001",
        "last_updated": "2026-06-01",
        "author": "产品经理-王芳",
        "snippet": "本次升级的核心目标是引入大模型对话能力，实现智能客服分流率达到70%。主要功能模块包括：大模型对话引擎、知识库检索增强（RAG）、智能路由分配、人工无缝转接...",
        "tags": ["PRD", "需求", "大模型", "客服"]
    },
    {
        "doc_id": "doc-002",
        "title": "大模型对话模块技术方案 v1.0",
        "type": "tech_spec",
        "project": "智能客服系统升级",
        "project_id": "proj-001",
        "last_updated": "2026-05-20",
        "author": "技术负责人-张伟",
        "snippet": "技术选型：采用LangChain + LangGraph实现多Agent协同架构。LLM层使用DeepSeek API，向量检索使用Milvus，协议层采用MCP标准。架构设计包括：对话管理Agent、知识检索Agent、意图识别模块...",
        "tags": ["技术方案", "架构", "LangChain", "MCP"]
    },
    {
        "doc_id": "doc-003",
        "title": "数据中台二期 ETL架构设计文档",
        "type": "tech_spec",
        "project": "数据中台建设二期",
        "project_id": "proj-002",
        "last_updated": "2026-03-10",
        "author": "数据架构师-孙六",
        "snippet": "ETL管道采用Apache Flink + Kafka实时流处理架构，批处理层使用Spark，数据湖基于MinIO构建。支持多数据源接入：MySQL、MongoDB、Kafka、REST API...",
        "tags": ["技术方案", "ETL", "数据架构", "Flink"]
    },
    {
        "doc_id": "doc-004",
        "title": "移动端App重构技术评估报告",
        "type": "tech_spec",
        "project": "移动端App重构",
        "project_id": "proj-003",
        "last_updated": "2026-04-15",
        "author": "技术负责人-李明",
        "snippet": "对比评估React Native、Flutter和原生方案。结论：推荐采用Flutter 3.x方案，优势在于热重载开发效率高、跨平台一致性优秀、Widget生态成熟。风险在于团队Flutter经验不足...",
        "tags": ["技术方案", "Flutter", "跨平台", "评估"]
    },
    {
        "doc_id": "doc-005",
        "title": "项目管理最佳实践指南",
        "type": "guide",
        "project": "通用",
        "project_id": None,
        "last_updated": "2026-01-01",
        "author": "PMO-陈总监",
        "snippet": "本文档定义了公司项目管理标准流程：需求评审→技术方案→Sprint规划→开发→测试→上线。每个阶段的检查清单、交付物标准和评审流程。包含风险管理框架：识别→评估→应对→监控的四步循环...",
        "tags": ["管理", "流程", "风险", "标准"]
    },
]

MOCK_MEETING_NOTES = [
    {
        "note_id": "note-001",
        "title": "2026-06-05 智能客服项目周会纪要",
        "date": "2026-06-05",
        "project_id": "proj-001",
        "attendees": ["张伟", "李四", "王芳", "赵五"],
        "key_decisions": [
            "确认6月20日为支付模块联调截止日",
            "同意从数据中台项目借调1名前端开发支援2周",
            "大模型API压力测试定于6月25日进行"
        ],
        "action_items": [
            {"assignee": "李四", "task": "完成支付SDK v3.0升级调研", "due": "2026-06-10", "status": "in_progress"},
            {"assignee": "赵五", "task": "准备GPU资源申请材料", "due": "2026-06-08", "status": "completed"},
            {"assignee": "王芳", "task": "更新PRD中大模型对话模块需求", "due": "2026-06-12", "status": "not_started"},
        ]
    },
    {
        "note_id": "note-002",
        "title": "2026-06-03 数据中台技术评审会纪要",
        "date": "2026-06-03",
        "project_id": "proj-002",
        "attendees": ["李明", "孙六", "周七"],
        "key_decisions": [
            "确认ETL管道采用Flink CDC方案替代Kafka Connect",
            "数据质量监控平台6月底完成MVP"
        ],
        "action_items": [
            {"assignee": "孙六", "task": "完成Flink CDC POC验证", "due": "2026-06-10", "status": "in_progress"},
            {"assignee": "周七", "task": "数据质量规则库设计", "due": "2026-06-15", "status": "not_started"},
        ]
    },
    {
        "note_id": "note-003",
        "title": "2026-05-30 项目管理月度复盘会",
        "date": "2026-05-30",
        "project_id": None,
        "attendees": ["陈总监", "张伟", "李明", "王芳", "各项目PM"],
        "key_decisions": [
            "所有项目即日起实施每周风险扫描机制",
            "项目健康度低于60分需向管理层提交改进方案",
            "6月起统一使用PM Agent工具进行周报管理"
        ],
        "action_items": [
            {"assignee": "各项目PM", "task": "完成6月第一周项目风险扫描", "due": "2026-06-09", "status": "pending"},
        ]
    },
]

MOCK_REPORT_DATA = {
    "proj-001": {
        "completed_tasks": [
            {"title": "需求评审文档定稿", "assignee": "王芳", "completed_date": "2026-06-03"},
            {"title": "大模型API选型评估", "assignee": "赵五", "completed_date": "2026-06-04"},
            {"title": "前端页面框架搭建", "assignee": "李四", "completed_date": "2026-06-05"},
        ],
        "in_progress_tasks": [
            {"title": "支付接口联调", "assignee": "李四", "progress": "60%"},
            {"title": "知识库向量索引优化", "assignee": "赵五", "progress": "40%"},
            {"title": "对话Agent Prompt优化", "assignee": "张伟", "progress": "75%"},
        ],
        "blocked_items": [
            {"title": "第三方支付SDK升级", "blocked_by": "等待厂商发布v3.0", "days": 5},
        ],
        "milestone_updates": [
            {"name": "需求评审", "status": "已完成（延期3天）"},
            {"name": "技术方案评审", "status": "进行中，预计按期完成"},
        ],
        "risks_and_issues": [
            "前端人力不足，已启动跨项目协调",
            "大模型API性能待验证",
        ],
        "team_workload": [
            {"member": "张伟", "role": "项目经理/架构", "utilization": 85, "current_tasks": 5},
            {"member": "李四", "role": "前端开发", "utilization": 95, "current_tasks": 7},
            {"member": "王芳", "role": "产品经理", "utilization": 70, "current_tasks": 4},
            {"member": "赵五", "role": "后端开发/AI", "utilization": 80, "current_tasks": 5},
        ],
        "next_period_plan": [
            "完成支付SDK升级调研",
            "启动大模型API压力测试",
            "完成技术方案评审",
        ]
    }
}


# ============================================================
# 工具定义
# ============================================================

@mcp.tool()
def search_documents(query: str, doc_type: Optional[str] = None) -> Dict[str, Any]:
    """搜索项目文档（PRD、技术方案、会议纪要、管理指南等）

    用于基于关键词搜索项目相关文档。支持按文档类型过滤。

    Args:
        query: 搜索查询词，支持关键词匹配（如 "PRD"、"大模型"、"技术方案"）
        doc_type: 文档类型过滤器
            - "prd": 产品需求文档
            - "tech_spec": 技术方案文档
            - "guide": 管理指南
            - 不传则搜索所有类型

    Returns:
        dict: 包含 total（匹配数量）和 documents（文档列表），
             每个文档含 doc_id/title/type/project/last_updated/snippet/author/tags
    """
    logger.info(f"[KnowledgeServer] search_documents(query={query}, doc_type={doc_type})")

    query_lower = query.lower()
    results = []

    for doc in MOCK_DOCUMENTS:
        # 类型过滤
        if doc_type and doc["type"] != doc_type:
            continue

        # 简单关键词匹配
        searchable = f"{doc['title']} {doc['snippet']} {' '.join(doc.get('tags', []))} {doc.get('project', '')}"
        if any(kw in searchable.lower() for kw in query_lower.split()):
            results.append(doc)

    return {
        "total": len(results),
        "documents": results
    }


@mcp.tool()
def get_document_content(doc_id: str) -> Dict[str, Any]:
    """获取指定项目文档的完整内容

    用于查看某个文档的全部内容，包括标题、正文和元数据。

    Args:
        doc_id: 文档ID，如 "doc-001" ~ "doc-005"

    Returns:
        dict: 包含 doc_id/title/content（Markdown格式全文）/metadata（类型/版本/作者等）
    """
    logger.info(f"[KnowledgeServer] get_document_content(doc_id={doc_id})")

    # 查找文档元数据
    doc_meta = None
    for doc in MOCK_DOCUMENTS:
        if doc["doc_id"] == doc_id:
            doc_meta = doc
            break

    if not doc_meta:
        return {"doc_id": doc_id, "title": "未找到", "content": "该文档不存在"}

    # Mock 完整文档内容
    contents = {
        "doc-001": """# 智能客服系统升级 PRD v2.1

## 1. 产品概述
升级现有客服工单系统，引入大模型对话能力实现智能客服分流。

### 1.1 核心目标
- 人工客服分流率从当前30%提升至70%
- 用户问题一次解决率 ≥ 80%
- 客服响应时间从5分钟降低至秒级

### 1.2 目标用户
- 外部用户：通过App/Web咨询的终端用户
- 内部用户：客服坐席（使用人工转接和辅助功能）

## 2. 核心功能

### 2.1 大模型对话引擎
- 支持多轮对话上下文管理（保留最近10轮）
- 支持知识库检索增强（RAG），从Milvus向量库检索相关文档
- 支持人工转接：当置信度 < 70% 时自动转人工

### 2.2 智能路由
- 基于用户意图自动分配技能组（售前/售后/技术）
- 支持优先级队列（VIP用户优先）

### 2.3 知识库管理
- 支持批量上传FAQ、产品手册、技术文档
- 自动化向量索引和定期更新

## 3. 非功能需求
- 响应时间 < 2s (P95)
- 并发支持 1000 QPS
- 可用性 99.9%（全年不超过8小时宕机）

## 4. 里程碑计划
| 里程碑 | 目标日期 | 关键交付物 |
|--------|---------|-----------|
| M1 需求评审完成 | 2026-06-15 | 评审通过的需求文档 |
| M2 技术方案评审 | 2026-06-30 | 技术方案文档、架构设计图 |
| M3 核心模块开发 | 2026-07-30 | 大模型对话引擎MVP |
| M4 联调测试 | 2026-08-10 | 集成测试报告 |
| M5 灰度上线 | 2026-08-15 | 灰度发布完成 |

## 5. 约束与假设
- 假设大模型API稳定性满足要求
- 约束：必须在Q3结束前完成上线
""",
        "doc-005": """# 项目管理最佳实践指南

## 1. 项目管理标准流程

### 项目启动→结项全流程
1. **需求评审**: PRD初稿 → 评审会议 → 修订 → 终稿确认（通常2周）
2. **技术方案**: 架构设计 → 技术选型 → 方案评审 → 确认（通常2周）
3. **Sprint规划**: 任务拆分 → 估时 → 分配 → Sprint Backlog（每2周）
4. **开发阶段**: 编码 → Code Review → 单元测试 → 提测（每Sprint）
5. **测试阶段**: 功能测试 → 集成测试 → 回归测试 → UAT（每Sprint）
6. **上线发布**: 预发布检查 → 灰度发布 → 全量上线 → 监控

## 2. 风险管理框架

### 2.1 风险识别
每个Sprint结束前进行风险扫描：
- 进度风险：里程碑延期、关键路径阻塞
- 资源风险：人员流失、技能缺口、预算超支
- 技术风险：技术方案不成熟、技术债务累积
- 外部风险：第三方依赖变更、合规要求

### 2.2 风险评估矩阵
| 影响/概率 | 低 (<20%) | 中 (20-50%) | 高 (>50%) |
|-----------|----------|------------|----------|
| 严重 (影响核心功能/延期>2周) | 中风险 🟡 | 高风险 🔴 | 极高风险 🔴🔴 |
| 中等 (影响次要功能/延期1-2周) | 低风险 🟢 | 中风险 🟡 | 高风险 🔴 |
| 轻微 (不影响交付/延期<1周) | 可忽略 ✅ | 低风险 🟢 | 中风险 🟡 |

### 2.3 风险应对策略
- **规避**: 修改项目计划，从根本上消除风险（如调整技术方案绕过技术难点）
- **缓解**: 采取措施降低风险概率或影响程度（如增加Code Review频率提升质量）
- **转移**: 将风险转移给第三方（如购买SaaS服务替代自建）
- **接受**: 制定应急计划，准备好风险发生时的应对措施

## 3. 健康度评分标准
| 维度 | 权重 | 评分依据 |
|------|------|---------|
| 进度 | 35% | 实际进度 vs 计划进度、里程碑达成率 |
| 质量 | 25% | 测试覆盖率、Bug密度、Code Review通过率 |
| 资源 | 25% | 团队利用率、关键角色备份、技能匹配度 |
| 风险 | 15% | 当前风险数量及严重程度 |

- 分数 >= 80: 🟢 健康 - 项目运行良好
- 分数 60-79: 🟡 需关注 - 存在问题需要改进
- 分数 < 60: 🔴 高风险 - 需要管理层介入

## 4. 周报规范
每周末前输出周报，包括：
1. 本周完成的关键任务
2. 下周计划
3. 风险和阻塞项
4. 需要管理层关注的事项
""",
    }

    content = contents.get(doc_id, f"# {doc_meta['title']}\n\n{doc_meta['snippet']}\n\n（完整内容请参考实际文档）")

    return {
        "doc_id": doc_id,
        "title": doc_meta["title"],
        "content": content,
        "metadata": {
            "type": doc_meta["type"],
            "project": doc_meta.get("project"),
            "author": doc_meta.get("author"),
            "last_updated": doc_meta.get("last_updated"),
        }
    }


@mcp.tool()
def list_meeting_notes(project_id: Optional[str] = None, days: int = 14) -> Dict[str, Any]:
    """查询最近的项目会议纪要列表

    用于了解最近的会议决策和待办事项。

    Args:
        project_id: 项目ID（可选，如 "proj-001"，不填则返回所有项目的会议纪要）
        days: 查询最近N天的会议纪要，默认14天

    Returns:
        dict: 包含 total（数量）和 notes（会议纪要列表），
             每个纪要含 note_id/title/date/project_id/attendees/key_decisions/action_items
    """
    logger.info(f"[KnowledgeServer] list_meeting_notes(project_id={project_id}, days={days})")

    cutoff_date = datetime.now() - timedelta(days=days)
    results = []

    for note in MOCK_MEETING_NOTES:
        note_date = datetime.strptime(note["date"], "%Y-%m-%d")
        if note_date < cutoff_date:
            continue
        if project_id and note.get("project_id") != project_id:
            continue
        results.append(note)

    return {
        "total": len(results),
        "notes": results
    }


@mcp.tool()
def aggregate_report_data(
    project_id: str,
    report_type: str = "weekly",
    period_start: Optional[str] = None,
    period_end: Optional[str] = None
) -> Dict[str, Any]:
    """聚合指定项目的日报或周报所需数据

    用于生成日报/周报时自动收集项目进展、任务完成情况和团队负载数据。

    Args:
        project_id: 项目ID，如 "proj-001", "proj-002", "proj-003"
        report_type: 报告类型 - "daily"（日报）或 "weekly"（周报），默认 "weekly"
        period_start: 周期开始日期 "YYYY-MM-DD"，不传则使用最近一周
        period_end: 周期结束日期 "YYYY-MM-DD"，不传则使用今天

    Returns:
        dict: 包含 project_id/report_period/data（completed_tasks/in_progress_tasks/
             blocked_items/milestone_updates/risks_and_issues/team_workload/next_period_plan）
    """
    logger.info(f"[KnowledgeServer] aggregate_report_data(project_id={project_id}, report_type={report_type})")

    # 计算报告周期
    today = datetime.now()
    if report_type == "daily":
        if not period_start:
            period_start = today.strftime("%Y-%m-%d")
        if not period_end:
            period_end = today.strftime("%Y-%m-%d")
    else:  # weekly
        if not period_start:
            period_start = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        if not period_end:
            period_end = today.strftime("%Y-%m-%d")

    # 获取项目的报告数据
    report_data = MOCK_REPORT_DATA.get(project_id, {
        "completed_tasks": [],
        "in_progress_tasks": [],
        "blocked_items": [],
        "milestone_updates": [],
        "risks_and_issues": [],
        "team_workload": [],
        "next_period_plan": [],
    })

    return {
        "project_id": project_id,
        "report_type": report_type,
        "report_period": f"{period_start} ~ {period_end}",
        "data": report_data
    }


# ============================================================
# 启动服务
# ============================================================

if __name__ == "__main__":
    logger.info("🚀 启动 PM Knowledge MCP Server (端口 8004)...")
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8004, path="/mcp")
