"""PM Agent 数据模型"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class PMRequest(BaseModel):
    """PM Agent 统一请求模型

    支持多种任务类型：
    - risk_scan: 项目风险扫描
    - health_check: 项目健康度评估
    - report: 日报/周报生成
    - doc_qa: 文档问答
    - auto: 自动分发（Dispatch Agent 识别意图）
    """
    session_id: Optional[str] = Field(
        default="default",
        description="会话ID，用于追踪对话历史"
    )
    task_type: Optional[str] = Field(
        default=None,
        description="任务类型: 'risk_scan', 'health_check', 'report', 'doc_qa', 'auto'"
    )
    project_id: Optional[str] = Field(
        default=None,
        description="目标项目ID，如 'proj-001'"
    )
    query: Optional[str] = Field(
        default=None,
        description="用户查询文本（用于 doc_qa 和 auto 模式）"
    )
    extra_params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="额外参数"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session-123",
                "task_type": "risk_scan",
                "project_id": "proj-001"
            }
        }
