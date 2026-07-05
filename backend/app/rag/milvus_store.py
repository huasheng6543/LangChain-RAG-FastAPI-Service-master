import asyncio
import os
import sys
from typing import Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import Field, ConfigDict
from pymilvus import connections, Collection, utility, FieldSchema, CollectionSchema, DataType

from app.utils.config import chroma_config
from app.utils.factory import embed_model
from app.core.logger_handler import logger

load_dotenv()


class MilvusRetriever(BaseRetriever):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    collection: Collection = Field(default=None)
    k: int = 5
    embed_model = None

    def __init__(self, collection, k=5, embed_model=None, **kwargs):
        super().__init__(collection=collection, k=k, embed_model=embed_model, **kwargs)
        self._collection = collection
        self._k = k
        self._embed_model = embed_model or embed_model

    def _get_relevant_documents(self, query: str, run_manager=None) -> list[Document]:
        if not self._embed_model:
            logger.error("【Milvus检索】嵌入模型未初始化")
            return []

        query_embedding = self._embed_model.embed_query(query)
        
        try:
            results = self._collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param={"metric_type": "L2", "params": {"nprobe": 10}},
                limit=self._k,
                output_fields=["content", "metadata"]
            )
            
            documents = []
            for hit in results[0]:
                content = hit.entity.get("content", "")
                metadata_str = hit.entity.get("metadata", "{}")
                try:
                    import json
                    metadata = json.loads(metadata_str)
                except:
                    metadata = {}
                documents.append(Document(page_content=content, metadata=metadata))
            return documents
        except Exception as e:
            logger.error(f"【Milvus检索】检索失败: {e}")
            return []


class MilvusVectorStoreService:
    def __init__(self):
        self.host = os.getenv("MILVUS_HOST", "localhost")
        self.port = os.getenv("MILVUS_PORT", "19530")
        self.collection_name = chroma_config['collection_name']
        self.embed_model = embed_model
        self.dim = self._get_embedding_dim()
        self.collection = None

    def _get_embedding_dim(self) -> int:
        try:
            sample_text = "测试"
            embedding = self.embed_model.embed_query(sample_text)
            return len(embedding)
        except Exception as e:
            logger.warning(f"【Milvus】获取嵌入维度失败，使用默认值768: {e}")
            return 768

    async def connect(self):
        try:
            await asyncio.to_thread(
                connections.connect,
                alias="default",
                host=self.host,
                port=self.port
            )
            logger.info(f"【Milvus】连接成功: {self.host}:{self.port}")
            await self._create_collection()
        except Exception as e:
            logger.error(f"【Milvus】连接失败: {e}")
            raise

    async def _create_collection(self):
        await asyncio.to_thread(self._sync_create_collection)

    def _sync_create_collection(self):
        if utility.has_collection(self.collection_name):
            self.collection = Collection(self.collection_name)
            logger.info(f"【Milvus】集合 {self.collection_name} 已存在，直接加载")
        else:
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=64, is_primary=True),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dim),
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=4096)
            ]
            schema = CollectionSchema(fields=fields, description="RAG知识库向量集合")
            self.collection = Collection(name=self.collection_name, schema=schema)
            
            index_params = {
                "metric_type": "L2",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024}
            }
            self.collection.create_index(field_name="embedding", index_params=index_params)
            logger.info(f"【Milvus】集合 {self.collection_name} 创建成功")
        
        self.collection.load()

    async def add_documents(self, documents: list[Document]):
        if not self.collection:
            await self.connect()

        import uuid
        import json
        
        ids = []
        embeddings = []
        contents = []
        metadatas = []

        for doc in documents:
            doc_id = str(uuid.uuid4())
            embedding = self.embed_model.embed_query(doc.page_content)
            
            ids.append(doc_id)
            embeddings.append(embedding)
            contents.append(doc.page_content[:65535])
            metadatas.append(json.dumps(doc.metadata, ensure_ascii=False)[:4096])

        try:
            await asyncio.to_thread(
                self.collection.insert,
                data=[ids, embeddings, contents, metadatas]
            )
            self.collection.flush()
            logger.info(f"【Milvus】成功插入 {len(documents)} 条文档")
        except Exception as e:
            logger.error(f"【Milvus】插入文档失败: {e}")
            raise

    async def delete(self, where: dict = None):
        if not self.collection:
            await self.connect()

        try:
            expr = ""
            if where:
                conditions = []
                for key, value in where.items():
                    if isinstance(value, str):
                        conditions.append(f'{key} == "{value}"')
                    else:
                        conditions.append(f'{key} == {value}')
                expr = " and ".join(conditions)
            
            if expr:
                await asyncio.to_thread(self.collection.delete, expr=expr)
                self.collection.flush()
                logger.info(f"【Milvus】删除文档成功，条件: {expr}")
        except Exception as e:
            logger.error(f"【Milvus】删除文档失败: {e}")
            raise

    async def get_retriever(self, k: int = 5) -> MilvusRetriever:
        if not self.collection:
            await self.connect()
        return MilvusRetriever(collection=self.collection, k=k, embed_model=self.embed_model)

    async def get(self, include: list = None):
        if not self.collection:
            await self.connect()

        try:
            results = await asyncio.to_thread(self.collection.query, expr="", output_fields=["content", "metadata"])
            documents = []
            import json
            for result in results:
                try:
                    metadata = json.loads(result.get("metadata", "{}"))
                except:
                    metadata = {}
                documents.append(Document(page_content=result.get("content", ""), metadata=metadata))
            return documents
        except Exception as e:
            logger.error(f"【Milvus】查询文档失败: {e}")
            return []

    async def close(self):
        try:
            await asyncio.to_thread(connections.disconnect, alias="default")
            logger.info("【Milvus】连接已关闭")
        except Exception as e:
            logger.error(f"【Milvus】关闭连接失败: {e}")