from datetime import datetime
from typing import Optional, List, Dict, Any
from app.models.assignment import Assignment, StudentAssignment, Question, QuestionOption, StudentResponse, QuestionType
from app.models.course import Course, StudentCourse
from app.react.tools_register import register_as_tool
from peewee import DoesNotExist, fn

class AssignmentService:
    """作业服务类，处理作业管理和学生作业提交。
    
    该服务提供作业相关的所有功能，包括作业创建、分发、提交、
    评分等功能。
    """
    
    @staticmethod
    def create_assignment(title, description, course_id, due_date, total_points=100.0):
        """创建新作业。
        
        Args:
            title (str): 作业标题
            description (str): 作业描述
            course_id (int): 课程ID
            due_date (datetime): 截止日期
            total_points (float): 总分，默认为100
            
        Returns:
            Assignment: 创建的作业对象
        """
        course = Course.get_by_id(course_id)
        return Assignment.create(
            title=title,
            description=description,
            course=course,
            due_date=due_date,
            total_points=total_points
        )
    
    @staticmethod
    def add_question(assignment_id, question_text, question_type, points=10.0, options=None):
        """向作业添加问题
        
        Args:
            assignment_id (int): 作业ID
            question_text (str): 问题文本
            question_type (str): 问题类型 (multiple_choice, fill_in_blank, short_answer)
            points (float): 分值，默认为10分
            options (list, optional): 选项列表 [{"text": "选项A", "is_correct": True}, ...]
            
        Returns:
            Question: 创建的问题对象
        """
        assignment = Assignment.get_by_id(assignment_id)
        
        # 获取当前最大的顺序值
        max_order = Question.select(fn.MAX(Question.order)).where(
            Question.assignment == assignment
        ).scalar()
        
        next_order = 1 if max_order is None else max_order + 1
        
        question = Question.create(
            assignment=assignment,
            question_text=question_text,
            question_type=question_type,
            points=points,
            order=next_order
        )
        
        # 如果是选择题，创建选项
        if question_type == QuestionType.MULTIPLE_CHOICE and options:
            for i, option in enumerate(options):
                QuestionOption.create(
                    question=question,
                    option_text=option['text'],
                    is_correct=option.get('is_correct', False),
                    order=i+1
                )
                
        return question
    
    @staticmethod
    def get_assignment_by_id(assignment_id):
        """获取作业详情
        Args:
            assignment_id (int): Assignment对象ID

        Returns:
            Assignment: 作业对象

        Raises:
            DoesNotExist: 如果作业不存在
        """
        return Assignment.get_by_id(assignment_id)
    
    @register_as_tool(roles=["teacher"])
    @staticmethod
    def get_assignment_questions(assignment_id):
        """获取作业的所有问题
        
        Args:
            assignment_id (int): 作业ID
            
        Returns:
            list: 问题对象列表，按顺序排序
        """
        return list(Question.select().where(
            Question.assignment_id == assignment_id
        ).order_by(Question.order))
    
    @register_as_tool(roles=["teacher"])
    @staticmethod
    def get_question_options(question_id):
        """获取问题的所有选项
        
        Args:
            question_id (int): 问题ID
            
        Returns:
            list: 选项对象列表，按顺序排序
        """
        return list(QuestionOption.select().where(
            QuestionOption.question_id == question_id
        ).order_by(QuestionOption.order))
    
    @staticmethod
    def assign_to_students(assignment_id):
        """将作业分配给所有选课学生。
        
        Args:
            assignment_id (int): 作业ID
            
        Returns:
            int: 分配的学生作业数量
        """
        assignment = Assignment.get_by_id(assignment_id)
        students = StudentCourse.select().where(StudentCourse.course == assignment.course)
        
        # 批量创建学生作业记录
        created = 0
        for student_course in students:
            if not StudentAssignment.select().where(
                (StudentAssignment.student == student_course.student) &
                (StudentAssignment.assignment == assignment)
            ).exists():
                StudentAssignment.create(
                    student=student_course.student,
                    assignment=assignment
                )
                created += 1
        
        return created
    
    @staticmethod
    def submit_response(student_id, question_id, answer_text=None, selected_option_id=None):
        """提交问题回答
        
        Args:
            student_id (int): 学生ID
            question_id (int): 问题ID
            answer_text (str, optional): 填空题或简答题的答案
            selected_option_id (int, optional): 选择题选中的选项ID
            
        Returns:
            StudentResponse: 学生回答对象
        """
        question = Question.get_by_id(question_id)
        assignment = question.assignment
        
        # 验证学生是否已加入课程
        enrollment = StudentCourse.select().where(
            (StudentCourse.student == student_id) &
            (StudentCourse.course == assignment.course)
        ).get_or_none()
        
        if not enrollment:
            raise ValueError("学生未加入课程")
        
        # 获取或创建学生作业记录
        student_assignment, created = StudentAssignment.get_or_create(
            student=enrollment.student,
            assignment=assignment
        )
        
        # 获取或创建学生回答记录
        student_response, created = StudentResponse.get_or_create(
            student_assignment=student_assignment,
            question=question
        )
        
        # 根据问题类型设置回答
        if question.question_type == QuestionType.MULTIPLE_CHOICE and selected_option_id:
            option = QuestionOption.get_by_id(selected_option_id)
            student_response.selected_option = option
            student_response.answer_text = None
        else:
            student_response.answer_text = answer_text
            student_response.selected_option = None
        
        student_response.save()
        
        # 更新学生作业记录
        student_assignment.submitted_at = datetime.now()
        student_assignment.attempts += 1
        student_assignment.save()
        
        return student_response
    
    @staticmethod
    def submit_assignment(student_id, assignment_id, answer=None, responses=None):
        """提交整个作业。
        
        Args:
            student_id (int): 学生用户ID
            assignment_id (int): 作业ID
            answer (str, optional): 传统作业答案（用于向后兼容）
            responses (dict, optional): 问题回答字典 {question_id: {answer_text/selected_option_id}}
            
        Returns:
            StudentAssignment: 更新后的学生作业对象
        """
        assignment = Assignment.get_by_id(assignment_id)
        enrollment = StudentCourse.select().where(
            (StudentCourse.student == student_id) &
            (StudentCourse.course == assignment.course)
        ).get_or_none()

        if not enrollment:
            raise ValueError("学生未加入课程")

        student = enrollment.student
        student_assignment, created = StudentAssignment.get_or_create(
            student = student,
            assignment = assignment
        )
        
        # 保存传统答案（向后兼容）
        if answer:
            student_assignment.answer = answer
        
        # 保存结构化回答
        if responses:
            for question_id, response_data in responses.items():
                if 'answer_text' in response_data:
                    AssignmentService.submit_response(
                        student_id=student_id,
                        question_id=question_id,
                        answer_text=response_data['answer_text']
                    )
                elif 'selected_option_id' in response_data:
                    AssignmentService.submit_response(
                        student_id=student_id,
                        question_id=question_id,
                        selected_option_id=response_data['selected_option_id']
                    )
        
        student_assignment.submitted_at = datetime.now()
        student_assignment.attempts += 1
        student_assignment.save()
        
        return student_assignment
    
    @register_as_tool(roles=["teacher"])
    @staticmethod
    def get_student_responses(student_id, assignment_id):
        """获取学生对作业的所有回答
        
        Args:
            student_id (int): 学生ID
            assignment_id (int): 作业ID
            
        Returns:
            dict: 回答字典 {question_id: student_response}
        """
        try:
            student_assignment = StudentAssignment.get(
                StudentAssignment.student_id == student_id,
                StudentAssignment.assignment_id == assignment_id
            )
            
            responses = StudentResponse.select().where(
                StudentResponse.student_assignment == student_assignment
            )
            
            # 构建问题ID到回答的映射
            response_dict = {}
            for response in responses:
                response_dict[response.question_id] = response
                
            return response_dict
        except DoesNotExist:
            return {}
    
    @register_as_tool(roles=["teacher"])
    @staticmethod
    def grade_question_response(student_id: int, question_id: int, score: float, feedback: str = None):
        """为问题回答评分
        
        Args:
            student_id (int): 学生ID
            question_id (int): 问题ID
            score (float): 分数
            feedback (str, optional): 反馈
            
        Returns:
            StudentResponse: 更新后的学生回答对象
            
        Raises:
            ValueError: 如果评分超过了问题的总分
        """
        question = Question.get_by_id(question_id)
        assignment = question.assignment
        
        # 检查评分是否超过问题的总分
        if score > question.points:
            raise ValueError(f"评分 ({score}) 不能超过问题的总分 ({question.points})")
        
        student_assignment = StudentAssignment.get(
            StudentAssignment.student_id == student_id,
            StudentAssignment.assignment_id == assignment.id
        )
        
        student_response = StudentResponse.get(
            StudentResponse.student_assignment == student_assignment,
            StudentResponse.question == question
        )
        
        student_response.score = score
        student_response.feedback = feedback
        student_response.save()
        
        # 更新总分
        AssignmentService.update_assignment_score(student_assignment.id)
        
        return student_response
    
    @staticmethod
    def update_assignment_score(student_assignment_id):
        """更新作业总分
        
        Args:
            student_assignment_id (int): 学生作业ID
            
        Returns:
            float: 计算出的总分
        """
        student_assignment = StudentAssignment.get_by_id(student_assignment_id)
        
        # 获取所有已评分的问题回答
        responses = StudentResponse.select().where(
            (StudentResponse.student_assignment == student_assignment) &
            (StudentResponse.score.is_null(False))
        )
        
        # 计算总分
        total_score = sum(response.score for response in responses)
        
        # 保存总分
        student_assignment.score = total_score
        
        # 检查是否所有问题都已评分
        assignment_questions = Question.select().where(
            Question.assignment == student_assignment.assignment
        )
        
        if responses.count() == assignment_questions.count():
            student_assignment.completed = True
            
        student_assignment.save()
        
        return total_score
    
    @register_as_tool(roles=["teacher"])
    @staticmethod
    def grade_assignment(student_id: int, assignment_id: int, score: float, feedback: str = Optional[str]):
        """为整个作业评分（向后兼容）

        Args:
            assignment_id (int): Assignment对象ID
            score (float): 评分
            feedback: 反馈
        
        Returns:
            StudentAssignment: 更新后的学生作业对象

        Raises:
            DoesNotExist: 如果找不到对应的作业对象
        """
        student_assignment = StudentAssignment.get(
            StudentAssignment.student==student_id,
            StudentAssignment.assignment==assignment_id
        )
        student_assignment.score = score
        student_assignment.feedback = feedback
        student_assignment.completed = True
        student_assignment.save()
        return student_assignment
    
    @register_as_tool(roles=["student", "teacher"])
    @staticmethod
    def get_student_assignments(student_id, course_id=None, completed=None):
        """获取学生的作业列表。
        
        Args:
            student_id (int): 学生用户ID
            course_id (int, optional): 课程ID，用于筛选指定课程的作业
            completed (bool, optional): 是否已完成，用于筛选作业状态
            
        Returns:
            list: 学生作业对象列表
        """
        query = StudentAssignment.select().where(StudentAssignment.student_id == student_id)
        
        if course_id:
            query = query.join(Assignment).where(Assignment.course_id == course_id)
            
        if completed is not None:
            query = query.where(StudentAssignment.completed == completed)
            
        return list(query)
    
    @register_as_tool(roles=["teacher"])
    @staticmethod
    def get_course_assignments(course_id):
        """获取课程的所有作业。
        
        Args:
            course_id (int): 课程ID
            
        Returns:
            list: 作业对象列表
        """
        return list(Assignment.select().where(Assignment.course_id == course_id))
