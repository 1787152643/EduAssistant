from app.models.course import Course, StudentCourse
from app.models.assignment import *
from app.models.user import User
from app.react.tools_register import register_as_tool
from app.ext import cache

class CourseService:
    """课程服务类，处理课程管理和学生课程关联。
    
    该服务提供课程相关的所有功能，包括课程创建、修改、删除，
    以及学生与课程之间的关联管理等。
    """
    @staticmethod
    def create_course(name, code, description, teacher_id):
        """创建新课程。
        
        Args:
            name (str): 课程名称
            code (str): 课程代码
            description (str): 课程描述
            teacher_id (int): 教师用户ID
            
        Returns:
            Course: 创建的课程对象
            
        Raises:
            ValueError: 如果课程代码已存在
        """
        if Course.select().where(Course.code == code).exists():
            raise ValueError(f"课程代码 '{code}' 已存在")
        
        teacher = User.get_by_id(teacher_id)
        course = Course.create(
            name=name,
            code=code,
            description=description,
            teacher=teacher
        )
        # 清除课程缓存
        cache.delete('all_courses')
        cache.delete_memoized(CourseService.get_courses_by_teacher, teacher_id)
        return course
    
    @staticmethod
    def enroll_student(course_id, student_id):
        """将学生加入课程。
        
        Args:
            course_id (int): 课程ID
            student_id (int): 学生ID
            
        Returns:
            StudentCourse: 创建的学生-课程关联对象
            
        Raises:
            ValueError: 如果学生已加入该课程
        """
        if StudentCourse.select().where(
            (StudentCourse.course_id == course_id) & 
            (StudentCourse.student_id == student_id)
        ).exists():
            raise ValueError("学生已加入该课程")
        
        student = User.get_by_id(student_id)
        course = Course.get_by_id(course_id)
        for assignment in course.assignments:
            StudentAssignment.create(
                student=student,
                assignment=assignment
            ).save()

        # 清除学生课程缓存
        cache.delete_memoized(CourseService.get_courses_by_student, student_id)
        
        return StudentCourse.create(
            course_id=course_id,
            student_id=student_id
        )
    
    @staticmethod
    def unenroll_student(course_id, student_id):
        """将学生从课程删除。
        
        Args:
            course_id (int): 课程ID
            student_id (int): 学生ID
            
        Returns:
            bool: 是否成功删除
            
        Raises:
            DoesNotExist: 如果学生没有加入课程
        """
        student_course = StudentCourse.select().where(
            (StudentCourse.course_id == course_id) & 
            (StudentCourse.student_id == student_id)
        ).get()

        for assignment in student_course.course.assignments:
            StudentAssignment.delete().where(
                StudentAssignment.student==student_id,
                StudentAssignment.assignment==assignment
            ).execute()

        # 清除学生课程缓存
        cache.delete_memoized(CourseService.get_courses_by_student, student_id)
        
        return student_course.delete_instance()

    @register_as_tool(roles=["student", "teacher"])
    @staticmethod
    @cache.cached(timeout=300, key_prefix='all_courses')
    def get_all_courses():
        """获取所有的课程

        Returns:
            list: 课程对象列表
        """
        return list(Course.select())
    
    @register_as_tool(roles=["teacher"])
    @staticmethod
    @cache.memoize(timeout=300)
    def get_courses_by_teacher(teacher_id):
        """获取教师所教授的所有课程。
        
        Args:
            teacher_id (int): 教师用户ID
            
        Returns:
            list: 课程对象列表
        """
        return list(Course.select().where(Course.teacher_id == teacher_id))
    
    @register_as_tool(roles=["student", "teacher"])
    @staticmethod
    @cache.memoize(timeout=300)
    def get_courses_by_student(student_id):
        """获取学生所参与的所有课程。
        
        Args:
            student_id (int): 学生用户ID
            
        Returns:
            list: 课程对象列表
        """
        return list(Course.select()
                   .join(StudentCourse)
                   .where(StudentCourse.student_id == student_id))
    
    @register_as_tool(roles=["teacher"])
    @staticmethod
    @cache.memoize(timeout=300)
    def get_students_by_course(course_id):
        """获取参与课程的所有学生。
        
        Args:
            course_id (int): 课程ID
            
        Returns:
            list: 学生用户对象列表
        """
        return list(User.select()
                   .join(StudentCourse)
                   .where(StudentCourse.course_id == course_id))
