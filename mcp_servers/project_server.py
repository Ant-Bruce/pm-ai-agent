"""
PM Project Server - 项目管理 MCP 服务（MOCK 数据）
提供项目查询、风险分析、健康度评估等工具
所有数据均为模拟数据，仅供演示使用
端口: 8003
"""

import json
import time
import random
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from fastmcp import FastMCP
from loguru import logger

mcp = FastMCP("ProjectManager")

# ============================================================
# Mock 数据
# ============================================================

MOCK_PROJECTS = [
    {
        "project_id": "proj-001",
        "name": "智能客服系统升级",
        "status": "at_risk",
        "health_score": 62,
        "progress_pct": 45,
        "deadline": "2026-08-15",
        "owner": "张伟",
        "team_size": 8,
        "description": "基于大模型的智能客服系统重构项目，目标将人工客服分流率提升至70%"
    },
    {
        "project_id": "proj-002",
        "name": "数据中台建设二期",
        "status": "active",
        "health_score": 78,
        "progress_pct": 68,
        "deadline": "2026-09-30",
        "owner": "李明",
        "team_size": 12,
        "description": "统一数据治理平台建设，整合多业务线数据源"
    },
    {
        "project_id": "proj-003",
        "name": "移动端App重构",
        "status": "paused",
        "health_score": 45,
        "progress_pct": 30,
        "deadline": "2026-07-31",
        "owner": "王芳",
        "team_size": 6,
        "description": "采用Flutter跨平台方案重构现有原生App"
    },
]

MOCK_MILESTONES = {
    "proj-001": [
        {"name": "需求评审完成", "planned_date": "2026-06-15", "actual_date": "2026-06-18", "status": "delayed", "delay_days": 3},
        {"name": "技术方案评审", "planned_date": "2026-06-30", "actual_date": None, "status": "on_track", "delay_days": 0},
        {"name": "核心模块开发", "planned_date": "2026-07-15", "actual_date": None, "status": "on_track", "delay_days": 0},
        {"name": "联调测试", "planned_date": "2026-08-10", "actual_date": None, "status": "at_risk", "delay_days": 0},
        {"name": "生产上线", "planned_date": "2026-08-15", "actual_date": None, "status": "at_risk", "delay_days": 0},
    ],
    "proj-002": [
        {"name": "数据模型设计", "planned_date": "2026-03-15", "actual_date": "2026-03-14", "status": "completed", "delay_days": -1},
        {"name": "ETL管道开发", "planned_date": "2026-05-30", "actual_date": "2026-06-02", "status": "delayed", "delay_days": 3},
        {"name": "数据质量平台", "planned_date": "2026-07-31", "actual_date": None, "status": "on_track", "delay_days": 0},
        {"name": "系统上线", "planned_date": "2026-09-30", "actual_date": None, "status": "on_track", "delay_days": 0},
    ],
    "proj-003": [
        {"name": "UI设计稿交付", "planned_date": "2026-04-30", "actual_date": "2026-05-10", "status": "delayed", "delay_days": 10},
        {"name": "Flutter框架搭建", "planned_date": "2026-05-30", "actual_date": "2026-05-28", "status": "completed", "delay_days": -2},
        {"name": "核心页面开发", "planned_date": "2026-06-30", "actual_date": None, "status": "paused", "delay_days": 0},
        {"name": "测试与发布", "planned_date": "2026-07-31", "actual_date": None, "status": "paused", "delay_days": 0},
    ],
}

MOCK_RISKS = {
    "proj-001": [
        {"category": "schedule", "risk": "里程碑'需求评审'延期3天，可能产生连锁效应", "severity": "high", "impact": "影响后续所有里程碑时间节点", "mitigation": "建议项目经理调整开发计划，增加资源投入追赶进度"},
        {"category": "resource", "risk": "前端开发人力不足，关键模块只有1名开发", "severity": "high", "impact": "可能成为开发阶段的瓶颈", "mitigation": "从数据中台项目协调1名前端开发支援"},
        {"category": "tech", "risk": "大模型API稳定性未经验证，存在性能风险", "severity": "medium", "impact": "可能影响系统响应时间目标", "mitigation": "提前进行压力测试，准备降级方案"},
    ],
    "proj-002": [
        {"category": "schedule", "risk": "ETL管道开发延期3天已完成，整体进度可控", "severity": "low", "impact": "已通过压缩后续任务时间追赶", "mitigation": "保持当前节奏，无需额外措施"},
        {"category": "resource", "risk": "数据工程师技能梯度大，code review效率偏低", "severity": "medium", "impact": "可能影响代码质量和交付速度", "mitigation": "安排高级工程师定期进行技术分享"},
    ],
    "proj-003": [
        {"category": "schedule", "risk": "UI设计延期10天导致整体项目暂停", "severity": "critical", "impact": "整个项目处于暂停状态，面临deadline风险", "mitigation": "需要管理层决策：增加设计资源或调整deadline"},
        {"category": "resource", "risk": "Flutter高级开发离职，团队只剩2名初级开发", "severity": "critical", "impact": "技术能力不足，无法继续推进", "mitigation": "紧急招聘或暂停项目重新评估"},
    ],
}

MOCK_BLOCKED_TASKS = {
    "proj-001": [
        {"task_id": "task-101", "title": "支付接口联调", "blocked_by": "等待第三方支付SDK v3.0升级", "blocked_days": 5, "assignee": "李四", "priority": "critical"},
        {"task_id": "task-102", "title": "大模型Prompt模板测试", "blocked_by": "等待GPU资源分配", "blocked_days": 3, "assignee": "赵五", "priority": "high"},
    ],
    "proj-002": [
        {"task_id": "task-201", "title": "实时数据同步模块", "blocked_by": "上游业务系统接口变更未通知", "blocked_days": 2, "assignee": "孙六", "priority": "medium"},
    ],
    "proj-003": [],
}


# ============================================================
# 工具定义
# ============================================================

@mcp.tool()
def list_all_projects(status_filter: Optional[str] = None) -> Dict[str, Any]:
    """获取所有项目列表及其基本状态

    当需要了解当前有哪些项目、项目状态（活跃/有风险/暂停/完成）时使用此工具。
    可以通过 status_filter 参数过滤特定状态的项目。

    Args:
        status_filter: 可选的状态过滤器
            - "active": 活跃项目
            - "at_risk": 有风险项目
            - "paused": 暂停项目
            - "completed": 已完成项目
            不传则返回所有项目

    Returns:
        dict: 包含 total（总数）和 projects（项目列表），每个项目含 project_id/name/status/health_score/progress_pct/deadline/owner/team_size/description
    """
    logger.info(f"[ProjectServer] list_all_projects(status_filter={status_filter})")

    projects = MOCK_PROJECTS
    if status_filter:
        projects = [p for p in projects if p["status"] == status_filter]

    return {
        "total": len(projects),
        "projects": projects
    }


@mcp.tool()
def get_milestones(project_id: str) -> Dict[str, Any]:
    """获取指定项目的里程碑列表及其状态

    用于查询项目的关键里程碑的完成情况，包括延期状态。

    Args:
        project_id: 项目ID，如 "proj-001", "proj-002", "proj-003"

    Returns:
        dict: 包含 project_id 和 milestones（里程碑列表），
             每个里程碑含 name/planned_date/actual_date/status/delay_days
    """
    logger.info(f"[ProjectServer] get_milestones(project_id={project_id})")

    milestones = MOCK_MILESTONES.get(project_id, [])
    return {
        "project_id": project_id,
        "milestones": milestones
    }


@mcp.tool()
def analyze_risks(project_id: str) -> Dict[str, Any]:
    """分析项目风险，包括进度风险、资源风险和技术风险

    用于全面评估项目的风险状况，自动计算风险等级。

    Args:
        project_id: 项目ID，如 "proj-001", "proj-002", "proj-003"

    Returns:
        dict: 包含 project_id/risk_level（low/medium/high/critical）和 risks（风险列表），
             每个风险含 category/risk/severity/impact/mitigation
    """
    logger.info(f"[ProjectServer] analyze_risks(project_id={project_id})")

    risks = MOCK_RISKS.get(project_id, [])
    if not risks:
        return {"project_id": project_id, "risk_level": "low", "risks": []}

    # 计算整体风险等级
    severity_scores = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    max_severity = max(severity_scores.get(r["severity"], 1) for r in risks)
    risk_level = ["low", "medium", "high", "critical"][max_severity - 1]

    return {
        "project_id": project_id,
        "risk_level": risk_level,
        "risks": risks
    }


@mcp.tool()
def calculate_health_score(project_id: str) -> Dict[str, Any]:
    """计算项目健康度评分（0-100），基于进度、质量、资源、风险四个维度

    用于综合评估项目的整体健康状况，自动打分并提供改进建议。

    Args:
        project_id: 项目ID，如 "proj-001", "proj-002", "proj-003"

    Returns:
        dict: 包含 project_id/overall_score（0-100）/dimensions（四个维度评分）
             /trend（improving/stable/declining）/recommendation（改进建议）
    """
    logger.info(f"[ProjectServer] calculate_health_score(project_id={project_id})")

    # 根据项目ID返回对应的健康度数据
    health_data = {
        "proj-001": {
            "overall_score": 62,
            "dimensions": {
                "progress":  {"score": 55, "weight": 0.35, "detail": "进度落后计划15%，需求评审延期3天"},
                "quality":   {"score": 70, "weight": 0.25, "detail": "代码测试覆盖率85%，PMD检查通过"},
                "resource":  {"score": 60, "weight": 0.25, "detail": "前端开发人力缺口，需要跨项目协调"},
                "risk":      {"score": 65, "weight": 0.15, "detail": "3个中度风险，其中1个为高风险"},
            },
            "trend": "declining",
            "recommendation": "建议立即补充前端开发资源并从数据中台项目协调1名工程师，同时重新评估里程碑时间线"
        },
        "proj-002": {
            "overall_score": 78,
            "dimensions": {
                "progress":  {"score": 82, "weight": 0.35, "detail": "整体进度超前2%，ETL管道延期已追赶"},
                "quality":   {"score": 75, "weight": 0.25, "detail": "code review效率待提升，代码质量良好"},
                "resource":  {"score": 80, "weight": 0.25, "detail": "团队规模充足，但技能梯度需要优化"},
                "risk":      {"score": 70, "weight": 0.15, "detail": "2个低-中风险，整体可控"},
            },
            "trend": "stable",
            "recommendation": "建议安排高级工程师进行技术分享，提升团队整体技能水平"
        },
        "proj-003": {
            "overall_score": 45,
            "dimensions": {
                "progress":  {"score": 35, "weight": 0.35, "detail": "项目暂停中，进度严重落后30%"},
                "quality":   {"score": 60, "weight": 0.25, "detail": "已完成部分代码质量尚可"},
                "resource":  {"score": 30, "weight": 0.25, "detail": "关键开发离职，团队只有2名初级开发"},
                "risk":      {"score": 55, "weight": 0.15, "detail": "2个极高风险，项目面临中止风险"},
            },
            "trend": "declining",
            "recommendation": "需要管理层紧急决策：招聘Flutter高级开发或考虑外包方案，否则建议暂停项目重新评估"
        },
    }

    return health_data.get(project_id, {
        "project_id": project_id,
        "overall_score": 0,
        "dimensions": {},
        "trend": "unknown",
        "recommendation": "未找到该项目"
    })


@mcp.tool()
def list_blocked_tasks(project_id: str) -> Dict[str, Any]:
    """获取指定项目中被阻塞的任务列表

    用于识别项目中的阻塞项，了解阻塞原因和影响。

    Args:
        project_id: 项目ID，如 "proj-001", "proj-002", "proj-003"

    Returns:
        dict: 包含 project_id/blocked_count/tasks（阻塞任务列表），
             每个任务含 task_id/title/blocked_by/blocked_days/assignee/priority
    """
    logger.info(f"[ProjectServer] list_blocked_tasks(project_id={project_id})")

    tasks = MOCK_BLOCKED_TASKS.get(project_id, [])
    return {
        "project_id": project_id,
        "blocked_count": len(tasks),
        "tasks": tasks
    }


@mcp.tool()
def get_project_progress(project_id: str) -> Dict[str, Any]:
    """获取项目详细进度数据，包括任务完成率和各阶段进展

    用于了解项目的整体进度和burn-down趋势。

    Args:
        project_id: 项目ID，如 "proj-001", "proj-002", "proj-003"

    Returns:
        dict: 包含 project_id/total_tasks/completed/in_progress/not_started/blocked/
             completion_pct/velocity（计划vs实际）/burndown（最近14天数据）
    """
    logger.info(f"[ProjectServer] get_project_progress(project_id={project_id})")

    # 根据项目ID返回不同的进度数据
    progress_data = {
        "proj-001": {"total_tasks": 45, "completed": 20, "in_progress": 15, "not_started": 8, "blocked": 2, "velocity_planned": 8, "velocity_actual": 6},
        "proj-002": {"total_tasks": 60, "completed": 41, "in_progress": 12, "not_started": 6, "blocked": 1, "velocity_planned": 10, "velocity_actual": 9},
        "proj-003": {"total_tasks": 35, "completed": 10, "in_progress": 3, "not_started": 22, "blocked": 0, "velocity_planned": 7, "velocity_actual": 2},
    }

    data = progress_data.get(project_id, {"total_tasks": 0, "completed": 0, "in_progress": 0, "not_started": 0, "blocked": 0, "velocity_planned": 0, "velocity_actual": 0})

    total = data["total_tasks"]
    completed = data["completed"]
    completion_pct = round(completed / total * 100, 1) if total > 0 else 0

    # 生成最近14天的燃尽图数据
    burndown = []
    remaining = total - completed
    today = datetime.now()
    for i in range(14, -1, -1):
        date = today - timedelta(days=i)
        burndown.append({
            "date": date.strftime("%Y-%m-%d"),
            "remaining": remaining + i * data["velocity_actual"]
        })

    return {
        "project_id": project_id,
        "total_tasks": total,
        "completed": completed,
        "in_progress": data["in_progress"],
        "not_started": data["not_started"],
        "blocked": data["blocked"],
        "completion_pct": completion_pct,
        "velocity": {
            "planned": data["velocity_planned"],
            "actual": data["velocity_actual"],
            "unit": "tasks/week"
        },
        "burndown": burndown
    }


# ============================================================
# 启动服务
# ============================================================

if __name__ == "__main__":
    logger.info("🚀 启动 PM Project MCP Server (端口 8003)...")
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8003, path="/mcp")
