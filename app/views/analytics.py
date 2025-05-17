from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for
from app.services.analytics_service import AnalyticsService
from app.services.course_service import CourseService
from app.models.user import User
from app.models.course import Course

from app.ext import cache

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')

@analytics_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    return render_template('analytics/index.html')

@analytics_bp.route('/student/<int:student_id>')
#@cache.cached(timeout=300)
def student_analytics(student_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    current_user = User.get_by_id(user_id)
    student = User.get_by_id(student_id)
    
    # 验证权限：只有学生本人或其教师才能查看
    is_teacher = False
    student_courses = CourseService.get_courses_by_student(student_id)
    for course in student_courses:
        if course.teacher_id == user_id:
            is_teacher = True
            break
    
    if user_id != student_id and not is_teacher:
        return redirect(url_for('dashboard.index'))
    
    # 获取学生的课程列表
    courses = CourseService.get_courses_by_student(student_id)
    
    # 默认选择第一个课程
    selected_course_id = request.args.get('course_id', None)
    if not selected_course_id and courses:
        selected_course_id = courses[0].id
    
    # 获取学习活动摘要
    activity_summary = AnalyticsService.get_student_activity_summary(
        student_id, 
        course_id=selected_course_id
    )
    
    # 知识点掌握情况
    knowledge_mastery = AnalyticsService.get_student_knowledge_mastery(
        student_id,
        course_id=selected_course_id
    )
    
    # 学习问题检测
    learning_issues = AnalyticsService.detect_learning_issues(
        student_id,
        course_id=selected_course_id
    )
    
    return render_template('analytics/student.html',
                          student=student,
                          courses=courses,
                          selected_course_id=int(selected_course_id) if selected_course_id else None,
                          activity_summary=activity_summary,
                          knowledge_mastery=knowledge_mastery,
                          learning_issues=learning_issues)

@analytics_bp.route('/course/<int:course_id>')
#@cache.cached(timeout=300)
def course_analytics(course_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    course = Course.get_by_id(course_id)
    
    # 验证权限：只有课程教师可以查看
    if course.teacher_id != user_id:
        return redirect(url_for('dashboard.index'))
    
    # 获取课程学生
    students = CourseService.get_students_by_course(course_id)
    
    # 收集所有学生的知识点掌握数据
    student_masteries = {}
    for student in students:
        mastery = AnalyticsService.get_student_knowledge_mastery(student.id, course_id)
        student_masteries[student.id] = mastery
    
    # 计算课程活跃度
    course_activity = {}
    for student in students:
        activity = AnalyticsService.get_student_activity_summary(student.id, course_id)
        course_activity[student.id] = activity
    
    return render_template('analytics/course.html',
                          course=course,
                          students=students,
                          student_masteries=student_masteries,
                          course_activity=course_activity)

@analytics_bp.route('/record-activity', methods=['POST'])
def record_activity():
    """记录学生学习活动的API端点"""
    if 'user_id' not in session:
        return jsonify(success=False, message="未登录"), 401
    
    data = request.json
    student_id = session['user_id']
    course_id = data.get('course_id')
    activity_type = data.get('activity_type')
    duration = int(data.get('duration', 0))
    knowledge_point_id = data.get('knowledge_point_id')
    metadata = data.get('metadata')
    
    try:
        AnalyticsService.record_learning_activity(
            student_id=student_id,
            course_id=course_id,
            activity_type=activity_type,
            duration=duration,
            knowledge_point_id=knowledge_point_id,
            metadata=metadata
        )
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e)), 400
