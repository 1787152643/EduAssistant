from flask import Blueprint, render_template, session, redirect, url_for, flash
from app.services.course_service import CourseService
from app.services.assignment_service import AssignmentService
from app.services.analytics_service import AnalyticsService
from app.services.user_service import UserService
from app.services.recommend_service import RecommendService
from app.models.user import User
from app.ext import cache

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@cache.cached(timeout=60, unless=lambda: 'user_id' not in session)
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
        recent_assignments = []
        for course in courses:
            assignments = AssignmentService.get_course_assignments(course.id)
            recent_assignments.extend(assignments)
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
