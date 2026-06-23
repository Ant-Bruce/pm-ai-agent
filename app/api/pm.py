"""
PM Agent API - 智能项目管理接口

提供统一的项目管理 Agent 入口，支持：
- 风险扫描 (risk_scan)
- 健康度评估 (health_check)
- 周报/日报生成 (report)
- 文档问答 (doc_qa)
- 自动分发 (auto)
"""

import json
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
from loguru import logger

from app.models.pm import PMRequest
from app.services.pm_service import pm_service

router = APIRouter()


@router.post("/pm")
async def pm_agent_stream(request: PMRequest):
    """PM Agent 统一入口（流式 SSE）

    **支持的任务类型：**

    | task_type | 说明 | 路由目标 |
    |-----------|------|---------|
    | `risk_scan` | 项目风险扫描 | Plan-Execute-Replan Agent |
    | `health_check` | 项目健康度评估 | Plan-Execute-Replan Agent |
    | `report` | 日报/周报生成 | Plan-Execute-Replan Agent |
    | `doc_qa` | 项目文档问答 | RAG Knowledge Agent |
    | `auto` / 不填 | 自动识别意图 | Dispatch Agent → 路由 |
    | `chat` | 通用对话 | Chat Agent |

    **SSE 事件类型：**

    - `plan` — 执行计划已制定
    - `step_complete` — 步骤执行完成
    - `status` — 状态更新
    - `report` — 最终报告
    - `content` — 流式文本内容（doc_qa/chat模式）
    - `complete` — 任务完成
    - `error` — 错误

    **使用示例：**
    ```bash
    # 风险扫描
    curl -X POST http://localhost:9900/api/pm \\
      -H "Content-Type: application/json" \\
      -d '{"session_id":"test","task_type":"risk_scan"}' --no-buffer

    # 周报生成
    curl -X POST http://localhost:9900/api/pm \\
      -H "Content-Type: application/json" \\
      -d '{"session_id":"test","task_type":"report","project_id":"proj-001"}' --no-buffer

    # 文档问答
    curl -X POST http://localhost:9900/api/pm \\
      -H "Content-Type: application/json" \\
      -d '{"session_id":"test","task_type":"doc_qa","query":"PRD中的里程碑计划是什么"}' --no-buffer

    # 自动分发
    curl -X POST http://localhost:9900/api/pm \\
      -H "Content-Type: application/json" \\
      -d '{"session_id":"test","query":"扫描项目风险"}' --no-buffer
    ```
    """
    session_id = request.session_id or "default"
    logger.info(f"[PM API {session_id}] 收到请求: task_type={request.task_type}, project_id={request.project_id}")

    async def event_generator():
        try:
            async for event in pm_service.handle_request(
                session_id=session_id,
                task_type=request.task_type,
                project_id=request.project_id,
                query=request.query
            ):
                yield {
                    "event": "message",
                    "data": json.dumps(event, ensure_ascii=False)
                }

                if event.get("type") in ["complete", "error"]:
                    break

            logger.info(f"[PM API {session_id}] 流式响应完成")

        except Exception as e:
            logger.error(f"[PM API {session_id}] 异常: {e}", exc_info=True)
            yield {
                "event": "message",
                "data": json.dumps({
                    "type": "error",
                    "stage": "exception",
                    "message": "服务内部错误，请稍后重试"
                }, ensure_ascii=False)
            }

    return EventSourceResponse(event_generator())
