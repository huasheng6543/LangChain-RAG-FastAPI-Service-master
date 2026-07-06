from abc import ABC, abstractmethod
from typing import Optional
import os
from dotenv import load_dotenv

from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_ollama import OllamaEmbeddings, ChatOllama

from app.utils.config import rag_config
from app.core.logger_handler import logger

# 加载环境变量
load_dotenv()


class BaseModelFactory(ABC):
    """基础模型工厂"""

    @abstractmethod
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        """生成模型"""
        pass


class ChatModelFactory(BaseModelFactory):
    """聊天模型工厂"""
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        """生成模型"""
        chat_model_type = os.getenv("CHAT_MODEL_TYPE", "aliyun").lower()
        
        if chat_model_type == "ollama":
            ollama_model = os.getenv("OLLAMA_CHAT_MODEL", "qwen3:7b")
            logger.info(f"【ChatModel】使用Ollama模型: {ollama_model}")
            return ChatOllama(
                model=ollama_model,
                base_url="http://localhost:11434",
                streaming=True,
                temperature=0.7,
                top_p=0.7,
            )
        else:
            return ChatTongyi(
                model=rag_config['chat_model_name'],
                api_key=os.getenv("ALIYUN_ACCESS_KEY_SECRET"),
                streaming=True,
                top_p=0.7,
            )


class EmbedModelFactory(BaseModelFactory):
    """嵌入模型工厂"""
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        """生成模型"""
        return OllamaEmbeddings(
            model=rag_config['text_embedding_model_name'],
            base_url="http://localhost:11434"
        )


class RerankerModelFactory(BaseModelFactory):
    """重排序模型工厂 - 已废弃，使用CrossEncoder模型"""
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        """生成模型"""
        # 注意：重排序服务已改为使用sentence_transformers的CrossEncoder模型
        # 这个工厂不再使用，保留仅为向后兼容
        return None


chat_model = ChatModelFactory().generator()
embed_model = EmbedModelFactory().generator()
# 重排序模型已改为使用CrossEncoder，不再使用Ollama模型
reranker_model = None