"""
Planner 节点：制定项目管理执行计划
基于 LangGraph 官方教程实现，适配 PM 领域
"""

from textwrap import dedent
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from app.core.llm_factory import llm_factory
from pydantic import BaseModel, Field
from loguru import logger

from app.config import config
from app.agent.tools_registry import get_all_tools
from app.agent.shared.state import PlanExecuteState
from app.agent.shared.utils import format_tools_description


class Plan(BaseModel):
    """计划的输出格式"""
    steps: List[str] = Field(
        description="完成任务所需的不同步骤。这些步骤应该按顺序执行，每一步都建立在前一步的基础上。"
    )


# PM Planner 提示词
planner_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            dedent("""
                作为一个专家级别的项目管理规划者，你需要将项目管理任务分解为可执行的步骤。

                可用工具列表（用于制定计划时参考）：

                {tools_description}

                注意：你的职责是制定计划，实际的工具调用由 Executor 负责执行。

                {experience_context}

                对于给定的任务，请创建一个简单的、逐步的计划来完成它。计划应该：
                - 将任务分解为逻辑上独立的步骤
                - 每个步骤应该明确使用哪些工具来获取信息，最好能同时提供工具执行所需要的参数
                - 步骤之间应该有清晰的依赖关系
                - 步骤描述要具体、可操作
                - **如果有相关经验文档，请参考其中的方法和步骤制定计划**

                示例输入："扫描当前项目的风险并生成风险报告"
                示例输出：
                步骤1: 使用 list_all_projects 工具获取所有活跃项目列表
                步骤2: 使用 get_project_progress 工具获取第一个项目的详细进度数据
                步骤3: 使用 analyze_risks 工具分析项目的进度风险、资源风险和技术风险
                步骤4: 使用 list_blocked_tasks 工具获取当前被阻塞的任务
                步骤5: 使用 calculate_health_score 工具计算项目健康度评分
                步骤6: 综合以上信息生成项目风险扫描报告

                示例输入："生成本周项目周报"
                示例输出：
                步骤1: 使用 get_current_time 工具获取当前时间，确定报告周期
                步骤2: 使用 list_all_projects 工具获取所有活跃项目
                步骤3: 使用 aggregate_report_data 工具聚合第一个项目的本周数据
                步骤4: 基于聚合数据生成结构化周报
            """).strip(),
        ),
        ("placeholder", "{messages}"),
    ]
)


async def planner(state: PlanExecuteState) -> Dict[str, Any]:
    """
    规划节点：根据用户输入生成执行计划

    流程：
    1. 先查询内部文档，获取相关经验和最佳实践
    2. 基于经验文档和可用工具制定执行计划
    """
    logger.info("=== PM Planner：制定执行计划 ===")

    input_text = state.get("input", "")
    logger.info(f"用户输入: {input_text}")

    try:
        # 步骤1: 查询内部文档获取相关经验
        logger.info("查询项目文档，寻找相关经验...")
        experience_docs = ""
        try:
            context_str = await retrieve_knowledge.ainvoke({"query": input_text})
            if context_str and context_str.strip():
                experience_docs = context_str
                logger.info(f"找到相关经验文档，长度: {len(experience_docs)}")
            else:
                logger.info("未找到相关经验文档")
        except Exception as e:
            logger.warning(f"查询内部文档失败: {e}")

        # 步骤2: 获取可用工具列表（含缓存）
        all_tools = await get_all_tools()
        logger.info(f"可用工具数量: {len(all_tools)}")

        # 格式化工具描述
        tools_description = format_tools_description(all_tools)

        # 步骤3: 格式化经验文档上下文
        if experience_docs:
            experience_context = dedent(f"""
                ## 相关项目管理文档

                以下是从知识库中检索到的相关经验和最佳实践，请参考这些经验制定执行计划：

                {experience_docs}

                ---
            """).strip()
        else:
            experience_context = ""

        # 步骤4: 创建 LLM 并生成计划
        from langchain_core.messages import SystemMessage

        llm = llm_factory.create_chat_model(
            model=config.dashscope_model,
            temperature=0,
            streaming=False
        )

        # 构建完整的 prompt 消息
        final_prompt = planner_prompt.format(
            messages=[],
            tools_description=tools_description,
            experience_context=experience_context
        )

        messages = [
            SystemMessage(content=final_prompt),
            SystemMessage(content="请直接输出一个 JSON 对象，格式为 {\"steps\": [\"步骤1\", \"步骤2\", ...]}。只输出纯 JSON，不要包含其他文字。")
        ]

        try:
            response = await llm.ainvoke(messages)
            response_text = response.content if hasattr(response, 'content') else str(response)

            # 尝试解析 JSON
            import json
            import re

            # 提取 JSON 块（可能被包裹在 ```json ``` 中）
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)

            plan_data = json.loads(response_text)
            plan_steps = plan_data.get("steps", [])

            if not plan_steps:
                raise ValueError("返回的步骤列表为空")

        except Exception as parse_error:
            logger.warning(f"JSON 解析失败: {parse_error}，使用文本行解析方案")
            # 回退：按行分割，提取数字开头的行作为步骤
            lines = response_text.strip().split('\n')
            plan_steps = []
            for line in lines:
                line = line.strip()
                # 匹配 "步骤N: ..." 或 "1. ..." 或 "- ..."
                if re.match(r'(步骤\d+[:：]|\d+[\.\)、]|[-*]\s)', line):
                    plan_steps.append(line)
            if not plan_steps:
                plan_steps = ["收集项目相关信息", "分析项目数据和风险", "生成项目管理报告"]

        logger.info(f"计划已生成，共 {len(plan_steps)} 个步骤")
        for i, step in enumerate(plan_steps, 1):
            logger.info(f"  步骤{i}: {step}")

        return {"plan": plan_steps}

    except Exception as e:
        logger.error(f"生成计划失败: {e}", exc_info=True)
        return {
            "plan": [
                "收集项目相关信息",
                "分析项目数据和风险",
                "生成项目管理报告"
            ]
        }
