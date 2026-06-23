"""向量嵌入服务模块 - 基于 LangChain Embeddings 标准接口"""

from typing import List

from langchain_core.embeddings import Embeddings
from openai import OpenAI
import requests
from loguru import logger

from app.config import config


class DashScopeEmbeddings(Embeddings):
    """阿里云 DashScope Text Embedding (OpenAI 兼容模式)
    
    实现 LangChain 标准 Embeddings 接口:
    - embed_documents(texts: List[str]) → List[List[float]]: 批量嵌入文档
    - embed_query(text: str) → List[float]: 嵌入单个查询
    """

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-v4",
        dimensions: int = 1024,
        base_url: str = "https://api.minimaxi.com/v1"
    ):
        """
        初始化 DashScope Embeddings
        
        Args:
            api_key: DashScope API Key
            model: 嵌入模型名称
            dimensions: 向量维度
            base_url: 接口地址
        """
        if not api_key or api_key == "your-api-key-here":
            raise ValueError("请设置环境变量对应 API_KEY")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model
        self.dimensions = dimensions
        
        # 打印初始化信息
        masked_key = self._mask_api_key(api_key)
        logger.info(
            f"DashScope Embeddings 初始化完成 - "
            f"模型: {model}, 维度: {dimensions}, API Key: {masked_key}"
        )

    @staticmethod
    def _mask_api_key(api_key: str) -> str:
        """掩码 API Key 用于日志"""
        if len(api_key) > 8:
            return f"{api_key[:8]}...{api_key[-4:]}"
        return "***"

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        批量嵌入文档列表 (LangChain 标准接口)
        
        Args:
            texts: 文本列表
            
        Returns:
            List[List[float]]: 嵌入向量列表
        """
        if not texts:
            return []
        
        try:
            logger.info(f"批量嵌入 {len(texts)} 个文档")
            
            if "minimax" in str(self.client.base_url):
                # 兼容 MiniMax 的嵌入接口
                res = requests.post(
                    f"{str(self.client.base_url).rstrip('/')}/embeddings",
                    headers={"Authorization": f"Bearer {self.client.api_key}", "Content-Type": "application/json"},
                    json={"model": self.model, "texts": texts, "type": "db"}
                )
                res_data = res.json()
                if "vectors" in res_data and res_data["vectors"]:
                    embeddings = res_data["vectors"]
                else:
                    raise RuntimeError(f"MiniMax 引擎 API 报错: {res_data}")
            else:
                # 批量调用 标准 API
                response = self.client.embeddings.create(
                    model=self.model,
                    input=texts,
                    dimensions=self.dimensions,
                    encoding_format="float"
                )
                embeddings = [item.embedding for item in response.data]

            logger.debug(f"批量嵌入完成, 维度: {len(embeddings[0])}")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"批量嵌入失败: {e}")
            raise RuntimeError(f"批量嵌入失败: {e}") from e

    def embed_query(self, text: str) -> List[float]:
        """
        嵌入单个查询文本 (LangChain 标准接口)
        
        Args:
            text: 查询文本
            
        Returns:
            List[float]: 嵌入向量
        """
        if not text or not text.strip():
            raise ValueError("查询文本不能为空")
        
        try:
            logger.debug(f"嵌入查询, 长度: {len(text)} 字符")
            
            if "minimax" in str(self.client.base_url):
                res = requests.post(
                    f"{str(self.client.base_url).rstrip('/')}/embeddings",
                    headers={"Authorization": f"Bearer {self.client.api_key}", "Content-Type": "application/json"},
                    json={"model": self.model, "texts": [text], "type": "query"}
                )
                res_data = res.json()
                if "vectors" in res_data and res_data["vectors"]:
                    embedding = res_data["vectors"][0]
                else:
                    raise RuntimeError(f"MiniMax 引擎 API 报错: {res_data}")
            else:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=text,
                    dimensions=self.dimensions,
                    encoding_format="float"
                )
                embedding = response.data[0].embedding
                
            logger.debug(f"查询嵌入完成, 维度: {len(embedding)}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"查询嵌入失败: {e}")
            raise RuntimeError(f"查询嵌入失败: {e}") from e


# 全局单例 (已替换为使用 SiliconFlow 免费向量接口)
vector_embedding_service = DashScopeEmbeddings(
    api_key=config.siliconflow_api_key or config.dashscope_api_key,
    model=config.siliconflow_embedding_model,
    dimensions=1024,
    base_url=config.siliconflow_api_base
)
