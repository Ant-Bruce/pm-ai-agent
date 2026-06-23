"""
Dispatch Agent - 意图识别和任务分发
根据用户输入将请求路由到合适的子 Agent
"""

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import Literal
from app.core.llm_factory import llm_factory
from app.config import config
from loguru import logger


class DispatchDecision(BaseModel):
    """Dispatch Agent 的任务分类结果"""
    agent_type: Literal["project_agent", "knowledge_agent", "report_agent", "chat_agent"] = Field(
        description="路由目标 Agent 类型"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="分类置信度 (0~1)"
    )
    reasoning: str = Field(
        default="",
        description="分类理由"
    )
    refined_query: str = Field(
        default="",
        description="优化后的查询文本（可选）"
    )


dispatch_prompt = ChatPromptTemplate.from_messages([
    ("system", """
你是一个智能调度助手，负责分析用户的请求并将其路由到正确的 AI Agent。

可用的 Agent 类型：

1. **project_agent** - 项目分析与计划执行Agent（Plan-Execute-Replan模式）
   - 处理：风险扫描、健康度评分、资源分析、进度检查、里程碑跟踪等需要多步推理的任务
   - 关键词：风险、扫描、分析、检查、评估、健康度、瓶颈、资源、进度、延期、里程碑

2. **knowledge_agent** - 知识库QA Agent（RAG模式）
   - 处理：基于项目文档的问答，如PRD内容查询、技术方案咨询、会议纪要搜索
   - 关键词：文档、PRD、需求、技术方案、会议纪要、规范、查询、查找、什么是、解释

3. **report_agent** - 报告生成Agent（模板驱动）
   - 处理：日报/周报生成、项目总结、状态报告
   - 关键词：周报、日报、总结、报告、汇报、汇总、导出

4. **chat_agent** - 通用对话Agent
   - 处理：闲聊、一般性问题、非项目管理的对话
   - 关键词：你好、帮助、谢谢、其他非项目管理话题

决策规则（按优先级）：
- 包含"风险"、"扫描"、"健康度"、"分析"、"检查"、"瓶颈" → project_agent
- 包含"周报"、"日报"、"报告"、"生成"、"总结"、"汇报" → report_agent
- 包含"文档"、"PRD"、"需求说明"、"技术方案"、"会议纪要"、"查询"、"是什么" → knowledge_agent
- 其他不明确的 → chat_agent
"""),
    ("user", "{query}")
])


async def dispatch(query: str) -> DispatchDecision:
    """
    分析用户请求并返回路由决策。

    Args:
        query: 用户输入的查询文本

    Returns:
        DispatchDecision: 包含目标 Agent 类型、置信度和优化查询
    """
    logger.info(f"=== Dispatch Agent：分析用户意图 ===")
    logger.info(f"用户查询: {query}")

    try:
        llm = llm_factory.create_chat_model(
            model=config.dashscope_model,
            temperature=0,
            streaming=False
        )

        chain = dispatch_prompt | llm.with_structured_output(DispatchDecision)
        decision = await chain.ainvoke({"query": query})

        if isinstance(decision, DispatchDecision):
            logger.info(f"分发决策: {decision.agent_type} (置信度: {decision.confidence:.2f})")
            logger.info(f"理由: {decision.reasoning}")
            return decision
        else:
            # 后备：默认为 chat_agent
            logger.warning("Dispatch 返回非预期格式，默认路由到 chat_agent")
            return DispatchDecision(
                agent_type="chat_agent",
                confidence=0.5,
                reasoning="Dispatch 异常，使用默认路由"
            )

    except Exception as e:
        logger.error(f"Dispatch 失败: {e}，默认路由到 chat_agent")
        return DispatchDecision(
            agent_type="chat_agent",
            confidence=0.3,
            reasoning=f"Dispatch 异常: {str(e)}"
        )
