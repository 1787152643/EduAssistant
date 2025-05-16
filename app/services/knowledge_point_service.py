from app.models.learning_data import (
    KnowledgePoint,
    AssignmentKnowledgePoint,
    KnowledgeBaseKnowledgePoint
)
from app.models.course import Course
from app.models.assignment import Assignment
from app.models.knowledge_base import KnowledgeBase
from typing import List, Dict, Optional
from peewee import DoesNotExist
from app.react.tools_register import register_as_tool
from app.ext import cache

class KnowledgePointService:

    @register_as_tool(roles=["teacher"])
    @staticmethod
    def create_knowledge_point(name: str, course_id: int, description: str = None, parent_id: int = None) -> KnowledgePoint:
        """创建一个新的知识点。
        
        Args:
            name: 知识点名称。
            course_id: 所属课程ID。
            description: 知识点描述，可选。
            parent_id: 父知识点ID，可选。
            
        Returns:
            KnowledgePoint: 新创建的知识点对象。
            
        Raises:
            ValueError: 当课程不存在或父知识点不存在或不属于同一课程时抛出。
        """
        try:
            course = Course.get_by_id(course_id)
            
            # 检查父知识点是否存在
            parent = None
            if parent_id:
                try:
                    parent = KnowledgePoint.get_by_id(parent_id)
                    # 确保父知识点属于同一课程
                    if parent.course_id != course_id:
                        raise ValueError("父知识点必须属于同一课程")
                except DoesNotExist:
                    raise ValueError(f"父知识点ID {parent_id} 不存在")
            
            # 创建知识点
            knowledge_point = KnowledgePoint.create(
                name=name,
                description=description,
                course=course,
                parent=parent
            )
            
            # 清除课程知识点缓存
            cache.delete_memoized(KnowledgePointService.get_course_knowledge_points, course_id)
            
            return knowledge_point
        
        except DoesNotExist:
            raise ValueError(f"课程ID {course_id} 不存在")

    @register_as_tool(roles=["student", "teacher"])
    @staticmethod
    @cache.memoize(timeout=300)
    def get_knowledge_point(knowledge_point_id: int) -> KnowledgePoint:
        """获取指定ID的知识点。
        
        Args:
            knowledge_point_id: 知识点ID。
            
        Returns:
            KnowledgePoint: 找到的知识点对象。
            
        Raises:
            ValueError: 当知识点不存在时抛出。
        """
        try:
            return KnowledgePoint.get_by_id(knowledge_point_id)
        except DoesNotExist:
            raise ValueError(f"知识点ID {knowledge_point_id} 不存在")

    @register_as_tool(roles=["student", "teacher"])
    @staticmethod
    @cache.memoize(timeout=300)
    def get_course_knowledge_points(course_id: int, include_tree: bool = False) -> List[KnowledgePoint]:
        """获取指定课程的所有知识点。
        
        Args:
            course_id: 课程ID。
            include_tree: 是否仅包含顶级知识点，默认为False。
            
        Returns:
            List[KnowledgePoint]: 知识点对象列表。
            
        Raises:
            ValueError: 当课程不存在时抛出。
        """
        try:
            Course.get_by_id(course_id)  # 验证课程是否存在
            
            if include_tree:
                # 仅获取顶级知识点
                top_level_points = KnowledgePoint.select().where(
                    (KnowledgePoint.course_id == course_id) & 
                    (KnowledgePoint.parent.is_null())
                )
                return list(top_level_points)
            else:
                # 获取所有知识点
                return list(KnowledgePoint.select().where(KnowledgePoint.course_id == course_id))
                
        except DoesNotExist:
            raise ValueError(f"课程ID {course_id} 不存在")

    @staticmethod
    def add_knowledge_points_to_assignment(
        assignment_id: int, 
        knowledge_point_ids: List[int],
        weights: Optional[Dict[int, float]] = None
    ) -> List[AssignmentKnowledgePoint]:
        """为作业关联知识点。
        
        Args:
            assignment_id: 作业ID。
            knowledge_point_ids: 知识点ID列表。
            weights: 知识点权重字典，键为知识点ID，值为权重，可选。
            
        Returns:
            List[AssignmentKnowledgePoint]: 新创建的关联对象列表。
            
        Raises:
            ValueError: 当作业不存在、知识点不存在或知识点不属于作业所在课程时抛出。
        """
        try:
            assignment = Assignment.get_by_id(assignment_id)
            course_id = assignment.course_id
            results = []
            
            for kp_id in knowledge_point_ids:
                try:
                    kp = KnowledgePoint.get_by_id(kp_id)
                    
                    # 确保知识点属于同一课程
                    if kp.course_id != course_id:
                        raise ValueError(f"知识点ID {kp_id} 不属于作业所在的课程")
                    
                    # 检查是否已经关联
                    try:
                        AssignmentKnowledgePoint.get(
                            assignment_id=assignment_id,
                            knowledge_point_id=kp_id
                        )
                        # 已存在关联，跳过
                        continue
                    except DoesNotExist:
                        # 不存在关联，创建新关联
                        weight = weights.get(kp_id, 1.0) if weights else 1.0
                        relation = AssignmentKnowledgePoint.create(
                            assignment=assignment,
                            knowledge_point=kp,
                            weight=weight
                        )
                        results.append(relation)
                
                except DoesNotExist:
                    raise ValueError(f"知识点ID {kp_id} 不存在")
            
            # 清除作业知识点缓存
            cache.delete_memoized(KnowledgePointService.get_assignment_knowledge_points, assignment_id)
            
            return results
            
        except DoesNotExist:
            raise ValueError(f"作业ID {assignment_id} 不存在")

    @staticmethod
    def add_knowledge_points_to_knowledge_base(
        knowledge_base_id: int, 
        knowledge_point_ids: List[int],
        weights: Optional[Dict[int, float]] = None
    ) -> List[KnowledgeBaseKnowledgePoint]:
        """为知识库条目关联知识点。
        
        Args:
            knowledge_base_id: 知识库条目ID。
            knowledge_point_ids: 知识点ID列表。
            weights: 知识点权重字典，键为知识点ID，值为权重，可选。
            
        Returns:
            List[KnowledgeBaseKnowledgePoint]: 新创建的关联对象列表。
            
        Raises:
            ValueError: 当知识库条目不存在、知识点不存在或知识点不属于知识库条目所在课程时抛出。
        """
        try:
            kb = KnowledgeBase.get_by_id(knowledge_base_id)
            course_id = kb.course_id if kb.course else None
            results = []
            
            for kp_id in knowledge_point_ids:
                try:
                    kp = KnowledgePoint.get_by_id(kp_id)
                    
                    # 如果知识库条目属于某个课程，确保知识点也属于同一课程
                    if course_id and kp.course_id != course_id:
                        raise ValueError(f"知识点ID {kp_id} 不属于知识库条目所在的课程")
                    
                    # 检查是否已经关联
                    try:
                        KnowledgeBaseKnowledgePoint.get(
                            knowledge_base_id=knowledge_base_id,
                            knowledge_point_id=kp_id
                        )
                        # 已存在关联，跳过
                        continue
                    except DoesNotExist:
                        # 不存在关联，创建新关联
                        weight = weights.get(kp_id, 1.0) if weights else 1.0
                        relation = KnowledgeBaseKnowledgePoint.create(
                            knowledge_base=kb,
                            knowledge_point=kp,
                            weight=weight
                        )
                        results.append(relation)
                
                except DoesNotExist:
                    raise ValueError(f"知识点ID {kp_id} 不存在")
            
            return results
            
        except DoesNotExist:
            raise ValueError(f"知识库条目ID {knowledge_base_id} 不存在")

    @staticmethod
    def remove_knowledge_point_from_assignment(assignment_id: int, knowledge_point_id: int) -> bool:
        """移除作业与知识点的关联。
        
        Args:
            assignment_id: 作业ID。
            knowledge_point_id: 知识点ID。
            
        Returns:
            bool: 如果成功删除关联返回True，如果关联不存在返回False。
        """
        try:
            relation = AssignmentKnowledgePoint.get(
                assignment_id=assignment_id,
                knowledge_point_id=knowledge_point_id
            )
            relation.delete_instance()
            return True
        except DoesNotExist:
            return False

    @staticmethod
    def remove_knowledge_point_from_knowledge_base(knowledge_base_id: int, knowledge_point_id: int) -> bool:
        """移除知识库条目与知识点的关联。
        
        Args:
            knowledge_base_id: 知识库条目ID。
            knowledge_point_id: 知识点ID。
            
        Returns:
            bool: 如果成功删除关联返回True，如果关联不存在返回False。
        """
        try:
            relation = KnowledgeBaseKnowledgePoint.get(
                knowledge_base_id=knowledge_base_id,
                knowledge_point_id=knowledge_point_id
            )
            relation.delete_instance()
            return True
        except DoesNotExist:
            return False

    @staticmethod
    @cache.memoize(timeout=300)
    def get_assignment_knowledge_points(assignment_id: int) -> List[Dict]:
        """获取作业关联的所有知识点。
        
        Args:
            assignment_id: 作业ID。
            
        Returns:
            List[Dict]: 包含知识点对象和权重的字典列表。
            
        Raises:
            ValueError: 当作业不存在时抛出。
        """
        try:
            Assignment.get_by_id(assignment_id)  # 验证作业是否存在
            
            query = (AssignmentKnowledgePoint
                     .select(AssignmentKnowledgePoint, KnowledgePoint)
                     .join(KnowledgePoint)
                     .where(AssignmentKnowledgePoint.assignment_id == assignment_id))
            
            results = []
            for relation in query:
                results.append({
                    'knowledge_point': relation.knowledge_point,
                    'weight': relation.weight
                })
            
            return results
            
        except DoesNotExist:
            raise ValueError(f"作业ID {assignment_id} 不存在")

    @staticmethod
    def get_knowledge_base_knowledge_points(knowledge_base_id: int) -> List[Dict]:
        """获取知识库条目关联的所有知识点。
        
        Args:
            knowledge_base_id: 知识库条目ID。
            
        Returns:
            List[Dict]: 包含知识点对象和权重的字典列表。
            
        Raises:
            ValueError: 当知识库条目不存在时抛出。
        """
        try:
            KnowledgeBase.get_by_id(knowledge_base_id)  # 验证知识库条目是否存在
            
            query = (KnowledgeBaseKnowledgePoint
                     .select(KnowledgeBaseKnowledgePoint, KnowledgePoint)
                     .join(KnowledgePoint)
                     .where(KnowledgeBaseKnowledgePoint.knowledge_base_id == knowledge_base_id))
            
            results = []
            for relation in query:
                results.append({
                    'knowledge_point': relation.knowledge_point,
                    'weight': relation.weight
                })
            
            return results
            
        except DoesNotExist:
            raise ValueError(f"知识库条目ID {knowledge_base_id} 不存在")
