"""配置管理模块

使用 Pydantic Settings 实现类型安全的配置管理
"""

from typing import Dict, Any
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 应用配置
    app_name: str = "PM_AI_Agent"
    app_version: str = "1.2.1"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 9900

    # CORS 配置（生产环境应设置具体域名，逗号分隔）
    cors_origins: str = "http://localhost:9900,http://127.0.0.1:9900"

    # DashScope / LLM 配置（支持 OpenAI 兼容 API，如 MiniMax、DeepSeek）
    dashscope_api_key: str = ""  # 默认空字符串，实际使用需从环境变量加载
    dashscope_api_base: str = "https://api.minimaxi.com/v1"  # 兼容 OpenAI 的 API 地址
    dashscope_model: str = "qwen-max"
    dashscope_embedding_model: str = "text-embedding-v4"  # v4 支持多种维度（默认 1024）

    # SiliconFlow Embedding 配置 (用于独立白嫖向量服务)
    siliconflow_api_key: str = ""  # 在 .env 中填入你的硅基流动 API Key
    siliconflow_api_base: str = "https://api.siliconflow.cn/v1"
    siliconflow_embedding_model: str = "BAAI/bge-m3"

    # Milvus 配置
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_timeout: int = 10000  # 毫秒

    # RAG 配置
    rag_top_k: int = 3

    # 文档分块配置
    chunk_max_size: int = 800
    chunk_overlap: int = 100

    # MCP 服务配置（PM Agent）
    mcp_project_transport: str = "streamable-http"
    mcp_project_url: str = "http://localhost:8003/mcp"
    mcp_knowledge_transport: str = "streamable-http"
    mcp_knowledge_url: str = "http://localhost:8004/mcp"

    @property
    def mcp_servers(self) -> Dict[str, Dict[str, Any]]:
        """获取完整的 MCP 服务器配置"""
        return {
            "project": {
                "transport": self.mcp_project_transport,
                "url": self.mcp_project_url,
            },
            "knowledge": {
                "transport": self.mcp_knowledge_transport,
                "url": self.mcp_knowledge_url,
            }
        }


# 全局配置实例
config = Settings()
