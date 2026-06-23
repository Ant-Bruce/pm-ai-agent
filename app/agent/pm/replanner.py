"""
Replanner 节点：重新规划或生成项目管理最终响应
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


class Response(BaseModel):
    """最终响应的格式"""
    response: str = Field(description="对用户的最终响应")


class Act(BaseModel):
    """重新规划的输出格式"""
    action: str = Field(
        description="""下一步的行动，必须是以下三种之一：
        - 'continue': 当前计划合理，继续执行下一个步骤
        - 'replan': 当前计划需要调整，提供新的步骤列表
        - 'respond': 计划已完成且信息充足，生成最终响应"""
    )
    new_steps: List[str] = Field(
        default_factory=list,
        description="新的步骤列表（如果 action 是 'replan'，这些步骤会替换剩余计划）"
    )


# PM Replanner 提示词
replanner_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            dedent("""
                作为一个项目管理分析专家，你需要根据已执行的步骤决定下一步行动。

                可用工具列表（用于制定计划时参考）：

                {tools_description}

                注意：你的职责是制定或调整计划，实际的工具调用由 Executor 负责执行。

                你有三个选择（按优先级排序）：

                **1. 'respond' - 信息充足，立即生成最终响应** 【最高优先级】
                   - 使用场景：当前信息已经足够回答用户项目管理问题
                   - 决策标准：
                     * 已执行步骤 >= 3 且获取了关键项目数据
                     * 或者已执行步骤 >= 5（无论结果如何）
                     * 或者当前信息完全满足任务需求
                   - ⚠️ 不要等到"完美"才响应，"足够好"就应该立即 respond

                **2. 'continue' - 当前计划合理，继续执行** 【次优先级】
                   - 使用场景：剩余计划合理且必要
                   - 决策标准：剩余步骤确实能提供关键的项目管理信息
                   - ⚠️ 如果剩余步骤不是"必需"的，应选择 respond

                **3. 'replan' - 当前计划有严重问题** 【最低优先级，谨慎使用】
                   - 使用场景：原计划明显错误或遗漏关键步骤
                   - ⚠️ **严格限制**：
                     * 新步骤数量必须 <= 当前剩余步骤数
                     * 优先简化计划，不要添加不必要的步骤
                     * 总步骤数已执行 >= 5 次时，禁止 replan，只能 respond

                评估标准：
                - 当前信息是否已经足够解决用户的项目管理问题？【最关键】
                - 已执行步骤是否成功获取了核心项目数据？
                - 剩余步骤是否真的"必需"？
                - 已执行步骤数是否过多（>= 5）？如果是，立即 respond

                **决策优先级口诀：**
                "优先结束 > 保持不变 > 调整计划"
                "信息足够就响应，不要追求完美"
            """).strip(),
        ),
        ("placeholder", "{messages}"),
    ]
)

# PM 最终响应生成提示词
response_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            dedent("""
                根据原始项目管理任务和已执行步骤的结果，生成一个全面的最终响应。

                响应要求：
                - 清晰、结构化的项目管理报告格式
                - 基于实际工具查询数据，不要编造
                - 如果某些步骤失败，要诚实说明
                - 使用 Markdown 格式
                - 包含可操作的改进建议和下一步行动
                - 如果涉及风险评估，使用 🔴/🟡/🟢 等级标注
                - 如果涉及进度，提供完成百分比和时间线
                - 如果涉及团队成员，标注负责人和截止日期
            """).strip(),
        ),
        ("placeholder", "{messages}"),
    ]
)


async def replanner(state: PlanExecuteState) -> Dict[str, Any]:
    """
    重新规划节点：决定是继续、调整计划还是生成最终响应

    三种决策：
    1. continue - 继续执行当前计划
    2. replan - 调整计划（替换剩余步骤）
    3. respond - 生成最终响应
    """
    logger.info("=== PM Replanner：重新规划 ===")

    input_text = state.get("input", "")
    plan = state.get("plan", [])
    past_steps = state.get("past_steps", [])

    logger.info(f"剩余计划步骤: {len(plan)}")
    logger.info(f"已执行步骤: {len(past_steps)}")

    # ⚠️ 强制限制：如果已执行步骤过多，直接生成响应
    MAX_STEPS = 8
    if len(past_steps) >= MAX_STEPS:
        logger.warning(f"已执行 {len(past_steps)} 个步骤，超过最大限制 {MAX_STEPS}，强制生成最终响应")
        llm = llm_factory.create_chat_model(
            model=config.dashscope_model,
            temperature=0,
            streaming=False
        )
        return await _generate_response(state, llm)

    # 获取可用工具列表
    try:
        all_tools = await get_all_tools()
        logger.info(f"可用工具数量: {len(all_tools)}")
        tools_description = format_tools_description(all_tools)
    except Exception as e:
        logger.warning(f"获取工具列表失败: {e}")
        tools_description = "无法获取工具列表"

    # 创建 LLM
    llm = llm_factory.create_chat_model(
        model=config.dashscope_model,
        temperature=0,
        streaming=False
    )

    # 格式化已执行的步骤
    steps_summary = "\n".join([
        f"步骤: {step}\n结果: {result[:300]}..."
        for step, result in past_steps
    ])

    # 如果还有剩余计划，进行决策
    if plan:
        logger.info("还有剩余计划，评估下一步行动")

        try:
            # 构建决策 prompt
            from langchain_core.messages import SystemMessage
            import json
            import re

            decision_prompt_text = replanner_prompt.format(
                messages=[],
                tools_description=tools_description
            )

            decision_messages = [
                SystemMessage(content=decision_prompt_text),
                SystemMessage(content=f"原始任务: {input_text}\n\n已执行的步骤:\n{steps_summary}\n\n剩余计划: {', '.join(plan)}\n\n⚠️ 重要提示：已执行 {len(past_steps)} 个步骤"),
                SystemMessage(content='请用 JSON 格式回复，只输出纯 JSON：\n- 继续执行: {"action": "continue"}\n- 调整计划: {"action": "replan", "new_steps": ["新步骤1", "新步骤2"]}\n- 生成响应: {"action": "respond"}')
            ]

            response = await llm.ainvoke(decision_messages)
            response_text = response.content if hasattr(response, 'content') else str(response)

            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                act_data = json.loads(json_match.group(0))
                action = act_data.get("action", "continue")
                new_steps = act_data.get("new_steps", [])
            else:
                logger.warning("无法解析决策 JSON，默认 continue")
                action = "continue"
                new_steps = []

            logger.info(f"Replanner 决策: {action}")

            if action == "respond":
                logger.info("决定生成最终响应")
                return await _generate_response(state, llm)

            elif action == "replan":
                if len(new_steps) > len(plan):
                    logger.warning(
                        f"新步骤数 {len(new_steps)} > 剩余步骤数 {len(plan)}，"
                        f"强制截断为 {len(plan)} 个步骤"
                    )
                    new_steps = new_steps[:len(plan)]

                if len(past_steps) >= 5:
                    logger.warning(f"已执行 {len(past_steps)} 个步骤，禁止重新规划，强制生成响应")
                    return await _generate_response(state, llm)

                logger.info(f"决定调整计划，新步骤数量: {len(new_steps)}")
                if new_steps:
                    return {"plan": new_steps}
                else:
                    logger.warning("replan 但未提供新步骤，继续执行原计划")
                    return {}

            else:  # action == "continue"
                logger.info("决定继续执行当前计划")
                return {}

        except Exception as e:
            logger.error(f"重新规划失败: {e}, 继续执行剩余计划")
            return {}

    else:
        # 没有剩余计划，生成最终响应
        logger.info("计划已执行完毕，生成最终响应")
        return await _generate_response(state, llm)


async def _generate_response(state: PlanExecuteState, llm: Any) -> Dict[str, Any]:
    """生成最终响应"""
    logger.info("生成最终响应...")

    input_text = state.get("input", "")
    past_steps = state.get("past_steps", [])

    # 格式化执行历史
    execution_history = "\n\n".join([
        f"### 步骤: {step}\n**结果:**\n{result}"
        for step, result in past_steps
    ])

    try:
        from langchain_core.messages import SystemMessage

        final_prompt_text = response_prompt.format(messages=[])
        messages = [
            SystemMessage(content=final_prompt_text),
            SystemMessage(content=f"原始任务: {input_text}\n\n执行历史:\n{execution_history}\n\n请基于以上信息生成全面的最终响应。使用 Markdown 格式。")
        ]

        response = await llm.ainvoke(messages)
        final_response = response.content if hasattr(response, 'content') else str(response)

        logger.info(f"最终响应生成完成，长度: {len(final_response)}")

        return {"response": final_response}

    except Exception as e:
        logger.error(f"生成响应失败: {e}")
        fallback_response = f"""# 项目管理任务执行结果

## 原始任务
{input_text}

## 执行的步骤
{_format_simple_steps(past_steps)}

## 说明
由于系统异常，无法生成完整响应。以上是已收集的信息。
"""
        return {"response": fallback_response}


def _format_simple_steps(past_steps: list) -> str:
    """格式化步骤列表（简单版）"""
    if not past_steps:
        return "无"

    formatted = []
    for i, (step, result) in enumerate(past_steps, 1):
        result_preview = result[:200] + "..." if len(result) > 200 else result
        formatted.append(f"{i}. **{step}**\n   {result_preview}\n")

    return "\n".join(formatted)
