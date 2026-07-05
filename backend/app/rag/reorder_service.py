from typing import List, Dict, Any
import torch
import os
from dotenv import load_dotenv
from sentence_transformers import CrossEncoder
from app.core.logger_handler import logger

# 加载环境变量
load_dotenv()


def check_and_download_reranker_model() -> None:
    """检查并重排序模型，在FastAPI启动时执行"""
    LOCAL_MODEL_PATH = os.getenv("RERANKER_MODEL_PATH", r"D:\Hugging_Face\models\Qwen3-Reranker-0.6B")
    HF_MODEL_NAME = "Qwen/Qwen3-Reranker-0.6B"
    
    try:
        # 检查本地模型是否存在
        if os.path.exists(LOCAL_MODEL_PATH) and os.path.isdir(LOCAL_MODEL_PATH):
            logger.info(f"✅ 检测到本地重排序模型：{LOCAL_MODEL_PATH}")
        else:
            logger.warning(f"⚠️  本地模型未找到：{LOCAL_MODEL_PATH}")
            logger.info(f"🔄 开始自动下载模型：{HF_MODEL_NAME}")
            
            # 创建模型目录
            os.makedirs(LOCAL_MODEL_PATH, exist_ok=True)
            
            # 自动下载模型
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model = CrossEncoder(
                HF_MODEL_NAME,
                max_length=512,
                device=device,
                cache_folder=LOCAL_MODEL_PATH
            )
            logger.info(f"✅ 模型下载完成，使用设备：{device}")
            
    except Exception as e:
        logger.error(f"❌ 模型检查失败: {str(e)}")
        raise RuntimeError(f"重排序模型检查失败: {str(e)}")


class ReorderService:
    """文档重排序服务"""
    
    def __init__(self):
        # 从环境变量读取重排序模型路径
        self.LOCAL_MODEL_PATH = os.getenv("RERANKER_MODEL_PATH", r"D:\Hugging_Face\models\Qwen3-Reranker-0.6B")
        # Hugging Face模型名称
        self.HF_MODEL_NAME = "Qwen/Qwen3-Reranker-0.6B"
        # 自动选择设备（优先使用GPU）
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        # 模型实例（懒加载）
        self._model = None
    
    async def _get_model(self):
        """懒加载模型实例"""
        if self._model is None:
            logger.info(f"✅ 加载重排序模型：{self.LOCAL_MODEL_PATH}")
            self._model = CrossEncoder(
                self.LOCAL_MODEL_PATH,
                max_length=512,
                device=self.device,
                local_files_only=True
            )
            # 强制使用评估模式，避免训练模式下的随机性
            self._model.eval()
            logger.info(f"✅ 模型加载成功，使用设备：{self.device}")
        return self._model
    
    @property
    async def model(self):
        """获取模型实例（懒加载）"""
        return await self._get_model()
    
    async def reorder_documents(self, query: str, documents: List[str], top_k: int = 3, score_threshold: float = -1.0) -> Dict[str, Any]:
        """
        对文档进行重排序
        :param query: 查询语句
        :param documents: 文档列表
        :param top_k: 返回前k个最相关的文档
        :param score_threshold: 分数阈值，低于此阈值的文档被过滤
        :return: 包含重排序结果的字典，格式为：
                 {"success": bool, "documents": List[Dict], "error": str, "metrics": Dict}
        """
        try:
            import time
            start_time = time.time()
            
            if not documents:
                return {
                    "success": True,
                    "documents": [],
                    "error": "",
                    "metrics": {"total_docs": 0, "filtered_docs": 0, "reorder_time_ms": 0}
                }
            
            pairs = [(query, doc) for doc in documents]
            
            model = await self.model
            with torch.no_grad():
                scores = model.predict(pairs, batch_size=4)
            
            scored_documents = []
            for doc, score in zip(documents, scores):
                scored_documents.append({
                    "document": doc,
                    "similarity": float(score)
                })
            
            sorted_docs = sorted(scored_documents, key=lambda x: x["similarity"], reverse=True)
            
            filtered_docs = [doc for doc in sorted_docs if doc["similarity"] >= score_threshold]
            
            final_docs = filtered_docs[:top_k]
            
            end_time = time.time()
            reorder_time_ms = int((end_time - start_time) * 1000)
            
            avg_score = sum(doc["similarity"] for doc in final_docs) / len(final_docs) if final_docs else 0
            max_score = max(doc["similarity"] for doc in final_docs) if final_docs else 0
            
            logger.info(f"【重排序服务】重排序完成 - 原始文档数: {len(documents)}, 过滤后: {len(filtered_docs)}, 返回: {len(final_docs)}, "
                      f"平均分数: {avg_score:.4f}, 最高分数: {max_score:.4f}, 耗时: {reorder_time_ms}ms")
            
            return {
                "success": True,
                "documents": final_docs,
                "error": "",
                "metrics": {
                    "total_docs": len(documents),
                    "filtered_docs": len(filtered_docs),
                    "returned_docs": len(final_docs),
                    "avg_score": avg_score,
                    "max_score": max_score,
                    "reorder_time_ms": reorder_time_ms
                }
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"【重排序服务】重排序失败: {error_msg}")
            return {
                "success": False,
                "documents": [],
                "error": error_msg,
                "metrics": {"total_docs": len(documents) if documents else 0, "filtered_docs": 0, "reorder_time_ms": 0}
            }

    @staticmethod
    async def format_reorder_result(sorted_docs: List[Dict]) -> str:
        """
        格式化重排序结果
        :param sorted_docs: 重排序后的文档列表
        :return: 格式化后的字符串
        """
        formatted_result = "重排序后的文档列表：\n"
        for i, doc in enumerate(sorted_docs, 1):
            formatted_result += f"{i}. 相似度: {doc.get('similarity', 0):.4f}\n"
            formatted_result += f"   内容: {doc.get('document', '')}\n\n"
        return formatted_result


# 全局重排序服务实例
reorder_service = ReorderService()