from app.models.knowledge_base import KnowledgeBase
from app.ext import knowledge_base_collection
import uuid

class KnowledgeBaseService:
    """知识库服务, 处理FAQ和知识内容的存储、检索。
    
    该服务提供知识库相关功能，包括添加知识条目、向量化存储和检索等。
    使用ChromaDB进行向量存储和语义检索。
    """
    
    @staticmethod
    def add_knowledge(title, content, course_id=None, category=None, tags=None):
        """添加知识条目到知识库。
        
        Args:
            title (str): 标题
            content (str): 内容
            course_id (int, optional): 关联的课程ID
            category (str, optional): 分类
            tags (list, optional): 标签列表
            
        Returns:
            KnowledgeBase: 创建的知识条目对象
        """
        # 创建数据库记录
        knowledge = KnowledgeBase.create(
            title=title,
            content=content,
            course_id=course_id,
            category=category,
            tags=tags
        )
        
        # 生成唯一ID
        vector_id = str(uuid.uuid4())
        knowledge.vector_id = vector_id
        knowledge.save()
        
        # 添加到向量数据库
        knowledge_base_collection.add(
            ids=[vector_id],
            documents=[content],
            metadatas=[{
                "id": knowledge.id,
                "title": title,
                "category": category or "",
                "course_id": course_id or 0,
                "tags": ",".join(tags) if tags else ""
            }]
        )
        
        return knowledge
    
    @staticmethod
    def search_knowledge(query, course_id=None, limit=5):
        """搜索知识库。
        
        Args:
            query (str): 查询文本
            course_id (int, optional): 课程ID，用于筛选指定课程的知识
            limit (int): 返回结果数量限制
            
        Returns:
            list: 匹配结果列表
        """
        # 使用ChromaDB搜索
        search_results = knowledge_base_collection.query(
            query_texts=[query],
            n_results=limit
        )
        
        results = []
        if len(search_results["ids"]) > 0:
            vector_ids_from_search = search_results["ids"][0]
            # Batch fetch KnowledgeBase records
            db_records_list = list(KnowledgeBase.select().where(KnowledgeBase.vector_id.in_(vector_ids_from_search)))
            db_records_map = {record.vector_id: record for record in db_records_list}

            for i, vector_id in enumerate(vector_ids_from_search):
                metadata = search_results["metadatas"][0][i]
                document = search_results["documents"][0][i]
                distance = None
                if "distances" in search_results:
                    distance = search_results["distances"][0][i]
                
                # 如果指定了课程筛选，检查是否匹配
                if course_id is not None and metadata["course_id"] != course_id:
                    continue
                
                # 获取完整记录 from the prefetched map
                db_record = db_records_map.get(vector_id)
                
                results.append({
                    "id": metadata["id"],
                    "title": metadata["title"],
                    "content": document,
                    "distance": distance,
                    "category": metadata["category"],
                    "course_id": metadata["course_id"],
                    "tags": metadata["tags"].split(",") if metadata["tags"] else [],
                    "full_record": db_record
                })
                
        return results
    
    @staticmethod
    def delete_knowledge(knowledge_id):
        """删除知识条目。
        
        Args:
            knowledge_id (int): 知识条目ID
            
        Returns:
            bool: 操作是否成功
        """
        knowledge = KnowledgeBase.get_or_none(id=knowledge_id)
        if not knowledge or not knowledge.vector_id:
            return False
            
        # 从向量数据库中删除
        try:
            knowledge_base_collection.delete(ids=[knowledge.vector_id])
        except:
            pass  # 即使向量删除失败也继续删除数据库记录
            
        # 删除数据库记录
        knowledge.delete_instance()
        return True
    
    @staticmethod
    def update_knowledge(knowledge_id, title=None, content=None, 
                        category=None, tags=None):
        """更新知识条目。
        
        Args:
            knowledge_id (int): 知识条目ID
            title (str, optional): 新标题
            content (str, optional): 新内容
            category (str, optional): 新分类
            tags (list, optional): 新标签列表
            
        Returns:
            KnowledgeBase: 更新后的知识条目对象
            
        Raises:
            ValueError: 如果找不到指定的知识条目
        """
        knowledge = KnowledgeBase.get_or_none(id=knowledge_id)
        if not knowledge:
            raise ValueError(f"知识条目ID {knowledge_id} 不存在")
            
        # 更新数据库记录
        if title is not None:
            knowledge.title = title
        if content is not None:
            knowledge.content = content
        if category is not None:
            knowledge.category = category
        if tags is not None:
            knowledge.tags = tags
            
        knowledge.save()
        
        # 如果内容或元数据变化，更新向量数据库
        if content is not None or title is not None or category is not None or tags is not None:
            if knowledge.vector_id:
                try:
                    # 删除旧向量
                    knowledge_base_collection.delete(ids=[knowledge.vector_id])
                except:
                    pass
                    
                # 添加新向量
                knowledge_base_collection.add(
                    ids=[knowledge.vector_id],
                    documents=[knowledge.content],
                    metadatas=[{
                        "id": knowledge.id,
                        "title": knowledge.title,
                        "category": knowledge.category or "",
                        "course_id": knowledge.course_id or 0,
                        "tags": ",".join(knowledge.tags) if knowledge.tags else ""
                    }]
                )
                
        return knowledge
