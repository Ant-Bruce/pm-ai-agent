"""
共享工具注册表
提供缓存的工具列表（本地工具 + MCP 工具），避免在各个 agent 节点中重复获取
"""

from typing import List
from loguru import logger

from app.tools import get_current_time, retrieve_knowledge
from app.agent.mcp_client import get_mcp_client

# 缓存的 MCP 工具列表
_mcp_tools_cache: List | None = None


async def get_all_tools() -> List:
    """获取所有可用工具（本地工具 + MCP 工具），MCP 工具会缓存在内存中

    Returns:
        List: 合并后的工具列表
    """
    global _mcp_tools_cache

    local_tools = [
        get_current_time,
        retrieve_knowledge
    ]

    # MCP 工具延迟加载并缓存
    if _mcp_tools_cache is None:
        mcp_client = await get_mcp_client()
        _mcp_tools_cache = await mcp_client.get_tools()
        logger.info(f"成功加载并缓存 {len(_mcp_tools_cache)} 个 MCP 工具")

    return local_tools + _mcp_tools_cache


def invalidate_mcp_tools_cache():
    """清除 MCP 工具缓存（用于测试或重新加载场景）"""
    global _mcp_tools_cache
    _mcp_tools_cache = None
    logger.info("MCP 工具缓存已清除")
