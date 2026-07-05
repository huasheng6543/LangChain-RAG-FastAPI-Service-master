import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.celery_config import app
from app.core.logger_handler import logger
from app.rag.vector_store import VectorStoreService
from app.utils.file_handler import get_file_md5_hex


@app.task(bind=True, max_retries=3, retry_backoff=2, retry_backoff_max=30)
def process_document_task(self, file_path: str, user_id: str = None):
    """
    异步处理文档并向量化
    
    Args:
        self: Celery任务实例
        file_path: 文件路径
        user_id: 用户ID
    
    Returns:
        处理结果
    """
    try:
        logger.info(f"【异步任务】开始处理文件: {file_path}, 用户ID: {user_id}")
        
        vector_store = VectorStoreService()
        
        md5_hex = get_file_md5_hex(file_path)
        
        if vector_store.check_md5_hex(md5_hex):
            logger.info(f"【异步任务】文件 {file_path} 的md5值 {md5_hex} 已存在，跳过")
            return {"status": "skipped", "message": "文件已存在", "file_path": file_path}
        
        document = vector_store.get_file_document(file_path)
        if not document:
            logger.error(f"【异步任务】文件 {file_path} 加载内容为空")
            return {"status": "failed", "message": "文件内容为空", "file_path": file_path}
        
        document = vector_store.spliter.split_documents(document)
        if not document:
            logger.error(f"【异步任务】文件 {file_path} 切分内容为空")
            return {"status": "failed", "message": "切分内容为空", "file_path": file_path}
        
        if user_id:
            for doc in document:
                doc.metadata['user_id'] = user_id
        
        vector_store.vectors_store.add_documents(document)
        vector_store.save_md5_hex(md5_hex)
        
        logger.info(f"【异步任务】文件 {file_path} 处理完成")
        return {"status": "success", "message": "处理完成", "file_path": file_path, "document_count": len(document)}
    
    except Exception as e:
        logger.error(f"【异步任务】处理文件 {file_path} 时出错: {e}")
        
        if self.request.retries < self.max_retries:
            logger.info(f"【异步任务】重试第 {self.request.retries + 1} 次")
            raise self.retry(exc=e, countdown=2 ** self.request.retries)
        
        logger.error(f"【异步任务】文件 {file_path} 处理失败，已达到最大重试次数")
        return {"status": "failed", "message": str(e), "file_path": file_path}


@app.task(bind=True, max_retries=3, retry_backoff=2)
def batch_process_documents_task(self, file_paths: list, user_id: str = None):
    """
    批量异步处理文档
    
    Args:
        self: Celery任务实例
        file_paths: 文件路径列表
        user_id: 用户ID
    
    Returns:
        处理结果汇总
    """
    results = []
    for file_path in file_paths:
        result = process_document_task.apply_async(args=[file_path, user_id])
        results.append({"file_path": file_path, "task_id": result.id})
    
    return {"status": "batch_started", "results": results}