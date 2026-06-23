"""
PM Service - 智能项目管理编排服务
整合 Dispatch Agent、Plan-Execute-Replan Agent、RAG Agent 和 Report Agent
"""

from textwrap import dedent
from typing import AsyncGenerator, Dict, Any, Optional

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from loguru import logger

from app.agent.pm import PlanExecuteState, planner, executor, replanner
from app.agent.pm.dispatch import dispatch, DispatchDecision
from app.services.rag_agent_service import rag_agent_service


# 节点名称常量
NODE_PLANNER = "planner"
NODE_EXECUTOR = "executor"
NODE_REPLANNER = "replanner"


class PlanExecuteService:
    """Plan-Execute-Replan 服务（通用版，被 PM Service 调用）"""

    def __init__(self):
        self.checkpointer = MemorySaver()
        self.graph = self._build_graph()
        logger.info("PM Plan-Execute-Replan Service 初始化完成")

    def _build_graph(self):
        """构建 Plan-Execute-Replan 工作流"""
        workflow = StateGraph(PlanExecuteState)
        workflow.add_node(NODE_PLANNER, planner)
        workflow.add_node(NODE_EXECUTOR, executor)
        workflow.add_node(NODE_REPLANNER, replanner)
        workflow.set_entry_point(NODE_PLANNER)
        workflow.add_edge(NODE_PLANNER, NODE_EXECUTOR)
        workflow.add_edge(NODE_EXECUTOR, NODE_REPLANNER)

        def should_continue(state: PlanExecuteState) -> str:
            if state.get("response"):
                return END
            if state.get("plan", []):
                return NODE_EXECUTOR
            return END

        workflow.add_conditional_edges(
            NODE_REPLANNER,
            should_continue,
            {NODE_EXECUTOR: NODE_EXECUTOR, END: END}
        )

        return workflow.compile(checkpointer=self.checkpointer)

    async def execute(
        self, user_input: str, session_id: str = "default"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """执行 Plan-Execute-Replan 流程"""
        logger.info(f"[PM PlanExecute {session_id}] 开始执行: {user_input}")

        try:
            initial_state: PlanExecuteState = {
                "input": user_input,
                "plan": [],
                "past_steps": [],
                "response": ""
            }

            config_dict = {"configurable": {"thread_id": session_id}}

            async for event in self.graph.astream(
                input=initial_state, config=config_dict, stream_mode="updates"
            ):
                for node_name, node_output in event.items():
                    if node_name == NODE_PLANNER:
                        plan = node_output.get("plan", []) if node_output else []
                        yield {
                            "type": "plan",
                            "stage": "plan_created",
                            "message": f"执行计划已制定，共 {len(plan)} 个步骤",
                            "plan": plan
                        }
                    elif node_name == NODE_EXECUTOR:
                        past_steps = node_output.get("past_steps", []) if node_output else []
                        plan = node_output.get("plan", []) if node_output else []
                        if past_steps:
                            last_step, _ = past_steps[-1]
                            yield {
                                "type": "step_complete",
                                "stage": "step_executed",
                                "message": f"步骤执行完成 ({len(past_steps)}/{len(past_steps) + len(plan)})",
                                "current_step": last_step,
                                "remaining_steps": len(plan)
                            }
                    elif node_name == NODE_REPLANNER:
                        response = node_output.get("response", "") if node_output else ""
                        plan = node_output.get("plan", []) if node_output else []
                        if response:
                            yield {
                                "type": "report",
                                "stage": "final_report",
                                "message": "最终报告已生成",
                                "report": response
                            }
                        else:
                            yield {
                                "type": "status",
                                "stage": "replanner",
                                "message": "评估完成，继续执行剩余步骤",
                                "remaining_steps": len(plan)
                            }

            final_state = self.graph.get_state(config_dict)
            final_response = ""
            if final_state and final_state.values:
                final_response = final_state.values.get("response", "")

            yield {
                "type": "complete",
                "stage": "complete",
                "message": "任务执行完成",
                "response": final_response
            }

        except Exception as e:
            logger.error(f"[PM PlanExecute {session_id}] 执行失败: {e}", exc_info=True)
            yield {
                "type": "error",
                "stage": "error",
                "message": f"任务执行出错: {str(e)}"
            }


class PMService:
    """PM Agent 总编排服务"""

    def __init__(self):
        self.plan_execute = PlanExecuteService()
        logger.info("PM Service 初始化完成")

    def _build_task_prompt(
        self, task_type: str, query: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> str:
        """根据任务类型构建对应的任务提示"""
        project_ref = f"项目 {project_id}" if project_id else "所有活跃项目"

        if task_type == "risk_scan":
            return dedent(f"""
                对{project_ref}进行全面的风险扫描并生成风险报告。

                报告格式要求：
                # 项目风险扫描报告

                ## 📊 项目概览
                项目基本信息、状态、健康度评分

                ## 🔴 风险清单（按严重程度排序）
                每个风险的类别、严重程度、影响和缓解措施

                ## 📋 阻塞任务
                当前被阻塞的任务及阻塞原因

                ## 📈 进度分析
                完成率、里程碑状态、燃尽图趋势

                ## 💡 改进建议
                具体可操作的改进措施，按优先级排列

                **重要提醒**：
                - 所有数据必须来自工具查询的真实数据，严禁编造
                - 如果某个步骤失败，在结论中如实说明
                - 使用 🔴/🟡/🟢 标注风险等级
            """).strip()

        elif task_type == "health_check":
            return dedent(f"""
                评估{project_ref}的健康度并生成健康度报告。

                报告格式要求：
                # 项目健康度评估报告

                ## 📊 综合评分
                总体健康度分数 (0-100) 及趋势

                ## 📐 四维评分
                - 进度维度（权重35%）：实际vs计划、里程碑达成率
                - 质量维度（权重25%）：测试覆盖率、Bug密度
                - 资源维度（权重25%）：团队负载、关键角色
                - 风险维度（权重15%）：风险数量和严重程度

                ## ⚠️ 主要问题
                影响健康度的关键问题

                ## 💡 改进建议
                提升健康度的具体措施

                **重要提醒**：
                - 使用 calculate_health_score 工具获取评分数据
                - 每个维度都要有具体的数据支撑
            """).strip()

        elif task_type == "report":
            return dedent(f"""
                为{project_ref}生成本周项目周报。

                报告格式要求：
                # 项目周报

                ## 📋 基本信息
                项目名称、报告周期、负责人

                ## ✅ 本周完成
                已完成的关键任务列表（含负责人和完成日期）

                ## 🔄 进行中
                正在进行的任务及当前进度

                ## 🚧 阻塞项
                被阻塞的任务、原因和需要的支持

                ## 🎯 里程碑状态
                各里程碑完成情况（完成/进行中/延期）

                ## ⚠️ 风险提示
                当前活跃风险及应对状态

                ## 👥 团队负载
                成员工作量分布和利用率

                ## 📝 下周计划
                下周的关键任务和里程碑目标

                **重要提醒**：
                - 使用 aggregate_report_data 工具获取本周数据
                - 数据要真实，不要编造
            """).strip()

        else:
            return query or "请分析项目管理情况"

    async def handle_request(
        self,
        session_id: str = "default",
        task_type: Optional[str] = None,
        project_id: Optional[str] = None,
        query: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        PM Agent 统一入口：分发 → 执行 → 流式返回
        """
        logger.info(f"[PM {session_id}] 收到请求: task_type={task_type}, project_id={project_id}")

        # Step 1: 确定路由
        if task_type and task_type != "auto":
            # 直接路由
            agent_type_map = {
                "risk_scan": "project_agent",
                "health_check": "project_agent",
                "report": "report_agent",
                "doc_qa": "knowledge_agent",
                "chat": "chat_agent",
            }
            agent_type = agent_type_map.get(task_type, "chat_agent")
        elif query:
            # 自动分发
            decision = await dispatch(query)
            agent_type = decision.agent_type
            if decision.refined_query:
                query = decision.refined_query
            logger.info(f"Dispatch → {agent_type} (置信度: {decision.confidence:.2f})")
        else:
            agent_type = "chat_agent"

        # Step 2: 路由到对应的 Agent
        if agent_type in ("project_agent", "report_agent"):
            # Plan-Execute-Replan Agent
            actual_task_type = task_type or ("report" if agent_type == "report_agent" else "risk_scan")
            task_prompt = self._build_task_prompt(actual_task_type, query, project_id)

            async for event in self.plan_execute.execute(task_prompt, session_id):
                yield event

        elif agent_type == "knowledge_agent":
            # RAG Knowledge Agent
            search_query = query or "查询项目文档"
            yield {
                "type": "status",
                "stage": "knowledge_search",
                "message": f"正在搜索知识库: {search_query}"
            }
            async for chunk in rag_agent_service.query_stream(
                search_query, session_id, agent_type="knowledge_agent"
            ):
                if chunk.get("type") == "content":
                    yield {
                        "type": "content",
                        "data": chunk.get("data", ""),
                        "node": "knowledge_agent"
                    }
                elif chunk.get("type") == "complete":
                    yield {"type": "complete", "message": "文档问答完成"}
                elif chunk.get("type") == "error":
                    yield {"type": "error", "message": chunk.get("data", "查询失败")}

        else:
            # Chat Agent
            chat_query = query or "你好"
            yield {
                "type": "status",
                "stage": "chat",
                "message": f"进入对话模式"
            }
            async for chunk in rag_agent_service.query_stream(
                chat_query, session_id, agent_type="chat_agent"
            ):
                if chunk.get("type") == "content":
                    yield {
                        "type": "content",
                        "data": chunk.get("data", ""),
                        "node": "chat_agent"
                    }
                elif chunk.get("type") == "complete":
                    yield {"type": "complete", "message": "对话完成"}
                elif chunk.get("type") == "error":
                    yield {"type": "error", "message": chunk.get("data", "对话失败")}


# 全局单例
pm_service = PMService()
