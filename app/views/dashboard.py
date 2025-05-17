from flask import Blueprint, render_template, session, redirect, url_for, flash
from app.services.course_service import CourseService
from app.services.assignment_service import AssignmentService
from app.services.analytics_service import AnalyticsService
from app.services.user_service import UserService
from app.services.recommend_service import RecommendService
from app.models.user import User
from app.models.course import Course
from app.models.assignment import Assignment

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    user = User.get_by_id(user_id)
    
    context = {
        'user': user
    }
    
    # 判断用户角色，显示不同仪表盘
    if UserService.has_role(user, 'teacher'):
        # 获取教师课程
        courses = CourseService.get_courses_by_teacher(user_id)
        context['courses'] = courses
        
        # 获取最近作业
        # Optimized to avoid N+1: Prefetch assignments if CourseService.get_courses_by_teacher doesn't already.
        # Assuming CourseService.get_courses_by_teacher returns a list of Course objects.
        # If assignments are not already prefetched by the service method,
        # we would ideally modify the service method.
        # For now, let's assume the service might not prefetch, and try to do it here if possible,
        # or acknowledge this as a place for potential service layer optimization.
        # A direct prefetch here on the result of a service call is tricky.
        # The best fix is within CourseService.get_courses_by_teacher or by changing how assignments are fetched.

        # Let's adjust how recent_assignments are collected to be more direct.
        # This still might be N queries if get_course_assignments is not optimized.
        # The ideal fix is to get all assignments for the teacher's courses in one go.
        
        # revised_courses = Course.select().where(Course.teacher == user_id).prefetch(Assignment)
        # recent_assignments = []
        # for course in revised_courses:
        #    recent_assignments.extend(list(course.assignments))

        # For a simpler immediate fix in the view, let's get all assignments for the teacher's courses
        course_ids = [c.id for c in courses]
        if course_ids:
            recent_assignments = list(Assignment.select().where(Assignment.course_id.in_(course_ids)))
        else:
            recent_assignments = []
            
        # 按截止日期排序，取前5个
        recent_assignments.sort(key=lambda x: x.due_date, reverse=True)
        context['recent_assignments'] = recent_assignments[:5]
        
        return render_template('dashboard/teacher_dashboard.html', **context)
    else:
        # 获取学生课程
        courses = CourseService.get_courses_by_student(user_id)
        context['courses'] = courses
        
        # 获取待完成作业
        incomplete_assignments = AssignmentService.get_student_assignments(user_id, completed=False)
        context['incomplete_assignments'] = incomplete_assignments
        
        # 获取学习活动摘要
        activity_summary = AnalyticsService.get_student_activity_summary(user_id)
        context['activity_summary'] = activity_summary
        
        # 获取学习问题警报
        learning_issues = AnalyticsService.detect_learning_issues(user_id)
        context['learning_issues'] = learning_issues
        
        return render_template('dashboard/student_dashboard.html', **context)

@dashboard_bp.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    user = User.get_by_id(user_id)
    
    return render_template('dashboard/profile.html', user=user)
