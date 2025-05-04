from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from app.services.course_service import CourseService
from app.services.assignment_service import AssignmentService
from app.services.user_service import UserService
from app.services.knowledge_point_service import KnowledgePointService
from app.models.user import User
from app.models.course import Course
from app.models.assignment import Assignment, Question, QuestionOption, QuestionType, StudentAssignment, StudentResponse
from datetime import datetime
import json

course_bp = Blueprint('course', __name__, url_prefix='/course')

@course_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    user = User.get_by_id(user_id)
    
    if UserService.has_role(user, 'teacher'):
        courses = CourseService.get_courses_by_teacher(user_id)
    else:
        courses = CourseService.get_all_courses()
        
    return render_template('course/index.html', courses=courses)

@course_bp.route('/create', methods=['GET', 'POST'])
def create():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']
    user = User.get_by_id(user_id)
    
    if not UserService.has_role(user, 'teacher'):
        flash('只有教师可以创建课程。', 'warning')
        return redirect(url_for('course.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        description = request.form.get('description')
        
        try:
            course = CourseService.create_course(
                name=name,
                code=code,
                description=description,
                teacher_id=user_id
            )
            flash(f'课程 "{name}" 创建成功!', 'success')
            return redirect(url_for('course.view', course_id=course.id))
        except ValueError as e:
            flash(str(e), 'danger')
    
    return render_template('course/create.html')

@course_bp.route('/<int:course_id>')
def view(course_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    course = Course.get_by_id(course_id)
    user_id = session['user_id']
    user = User.get_by_id(user_id)
    
    # 确认用户是课程的教师或学生
    is_teacher = course.teacher_id == user_id
    is_student = False
    
    if not is_teacher:
        student_courses = CourseService.get_courses_by_student(user_id)
        if course_id in [c.id for c in student_courses]:
            is_student = True
    
    '''if not (is_teacher or is_student):
        flash('您没有访问该课程的权限。', 'warning')
        return redirect(url_for('course.index'))'''
    
    # 获取课程作业
    assignments = AssignmentService.get_course_assignments(course_id)
    
    # 获取课程知识点
    knowledge_points = KnowledgePointService.get_course_knowledge_points(course_id)
    
    # 如果是教师，获取学生列表
    students = None
    if is_teacher:
        students = CourseService.get_students_by_course(course_id)
    
    # 如果是学生，获取个人作业情况
    student_assignments = None
    if is_student:
        student_assignments = AssignmentService.get_student_assignments(user_id, course_id)
    
    return render_template('course/view.html',
                         course=course,
                         is_teacher=is_teacher,
                         is_student=is_student,
                         assignments=assignments,
                         students=students,
                         student_assignments=student_assignments,
                         knowledge_points=knowledge_points)

@course_bp.route('/<int:course_id>/enroll', methods=['GET', 'POST'])
def enroll(course_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    user = User.get_by_id(user_id)
    
    if not UserService.has_role(user, 'student'):
        flash('只有学生可以加入课程。', 'warning')
        return redirect(url_for('course.index'))
    
    course = Course.get_by_id(course_id)
    
    if request.method == 'POST':
        try:
            CourseService.enroll_student(course_id, user_id)
            flash(f'成功加入课程 "{course.name}"!', 'success')
        except ValueError as e:
            flash(str(e), 'warning')
        
        return redirect(url_for('course.view', course_id=course_id))
    
    return render_template('course/enroll.html', course=course)

@course_bp.route('/unenroll/<int:course_id>', methods=['POST'])
def unenroll(course_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    # 检查用户是否已加入该课程
    user_id = session['user_id']
    try:
        if CourseService.unenroll_student(course_id, user_id):
            flash(f'您已成功退出课程', 'success')
        else:
            flash(f'退出课程失败', 'warning')
    except Exception as e:
        flash(str(e), 'warning')
    
    return redirect(url_for('course.view', course_id=course_id))

@course_bp.route('/<int:course_id>/assignment/create', methods=['GET', 'POST'])
def create_assignment(course_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    course = Course.get_by_id(course_id)
    
    # 验证权限
    if course.teacher_id != user_id:
        flash('只有课程教师可以创建作业。', 'warning')
        return redirect(url_for('course.view', course_id=course_id))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        due_date = datetime.fromisoformat(request.form.get('due_date'))
        total_points = float(request.form.get('total_points', 100))
        
        # 创建作业基本信息
        assignment = AssignmentService.create_assignment(
            title=title,
            description=description,
            course_id=course_id,
            due_date=due_date,
            total_points=total_points
        )
        
        # 处理问题部分
        questions_data = request.form.get('questions_data')
        if questions_data:
            questions = json.loads(questions_data)
            for question_data in questions:
                question_type = question_data.get('type')
                question_text = question_data.get('text')
                points = float(question_data.get('points', 10))
                
                # 根据问题类型创建不同的问题
                if question_type == QuestionType.MULTIPLE_CHOICE:
                    options = question_data.get('options', [])
                    AssignmentService.add_question(
                        assignment_id=assignment.id,
                        question_text=question_text,
                        question_type=question_type,
                        points=points,
                        options=options
                    )
                else:
                    AssignmentService.add_question(
                        assignment_id=assignment.id,
                        question_text=question_text,
                        question_type=question_type,
                        points=points
                    )
        
        # 自动分配给所有学生
        assigned_count = AssignmentService.assign_to_students(assignment.id)
        
        flash(f'作业已创建并分配给{assigned_count}名学生。', 'success')
        return redirect(url_for('course.view', course_id=course_id))
    
    return render_template('course/create_assignment.html', course=course)

@course_bp.route('/assignment/<int:assignment_id>')
def view_assignment(assignment_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    assignment = Assignment.get_by_id(assignment_id)
    user_id = session['user_id']
    
    # 检查权限
    is_teacher = assignment.course.teacher_id == user_id
    student_assignment = None
    
    if not is_teacher:
        student_assignment = StudentAssignment.get_or_none(
            StudentAssignment.student_id == user_id,
            StudentAssignment.assignment_id == assignment_id
        )
        '''if not student_assignment:
            flash('您没有访问该作业的权限。', 'warning')
            return redirect(url_for('course.index'))'''
    
    # 如果是教师，获取所有学生提交情况
    submissions = None
    if is_teacher:
        submissions = StudentAssignment.select().where(
            StudentAssignment.assignment_id == assignment_id
        )
    
    # 获取作业关联的知识点
    knowledge_points = KnowledgePointService.get_assignment_knowledge_points(assignment_id)
    
    # 获取作业的问题
    questions = AssignmentService.get_assignment_questions(assignment_id)
    
    # 对于每个问题，如果是选择题，获取选项
    for question in questions:
        if question.question_type == QuestionType.MULTIPLE_CHOICE:
            question.options = AssignmentService.get_question_options(question.id)
    
    # 获取学生的回答
    student_responses = {}
    if student_assignment:
        student_responses = AssignmentService.get_student_responses(user_id, assignment_id)
    
    return render_template('course/view_assignment.html',
                         assignment=assignment,
                         is_teacher=is_teacher,
                         student_assignment=student_assignment,
                         submissions=submissions,
                         knowledge_points=knowledge_points,
                         questions=questions,
                         student_responses=student_responses)

@course_bp.route('/assignment/<int:assignment_id>/submit', methods=['POST'])
def submit_assignment(assignment_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    
    # 处理兼容旧版的纯文本回答
    answer = request.form.get('content')
    
    # 处理新的结构化问题回答
    questions = AssignmentService.get_assignment_questions(assignment_id)
    responses = {}
    
    for question in questions:
        if question.question_type == QuestionType.MULTIPLE_CHOICE:
            option_id = request.form.get(f'question_{question.id}_option')
            if option_id:
                responses[question.id] = {'selected_option_id': int(option_id)}
        else:
            answer_text = request.form.get(f'question_{question.id}_answer')
            if answer_text:
                responses[question.id] = {'answer_text': answer_text}
    
    try:
        AssignmentService.submit_assignment(
            user_id, 
            assignment_id, 
            answer=answer, 
            responses=responses
        )
        flash('作业已提交。', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    
    return redirect(url_for('course.view_assignment', assignment_id=assignment_id))

@course_bp.route('/assignment/<int:assignment_id>/submission/<int:student_id>', methods=['GET'])
def view_submission(assignment_id, student_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']
    assignment = AssignmentService.get_assignment_by_id(assignment_id)
    
    # 验证权限
    if assignment.course.teacher_id != user_id and user_id != student_id:
        flash('您没有权限查看此提交。', 'warning')
        return redirect(url_for('course.view_assignment', assignment_id=assignment_id))
    
    student = User.get_by_id(student_id)
    submission = StudentAssignment.get(
        StudentAssignment.student==student,
        StudentAssignment.assignment==assignment
    )
    
    # 获取作业的问题
    questions = AssignmentService.get_assignment_questions(assignment_id)
    
    # 获取学生的回答
    student_responses = AssignmentService.get_student_responses(student_id, assignment_id)
    
    # 对于每个问题，如果是选择题，获取选项
    for question in questions:
        if question.question_type == QuestionType.MULTIPLE_CHOICE:
            question.options = AssignmentService.get_question_options(question.id)

    return render_template('course/view_submission.html', 
                          assignment=assignment, 
                          student=student,
                          submission=submission,
                          questions=questions,
                          student_responses=student_responses)

@course_bp.route('/assignment/<int:assignment_id>/grade/<int:student_id>', methods=['POST'])
def grade_assignment(assignment_id, student_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    assignment = Assignment.get_by_id(assignment_id)
    
    # 验证权限
    if assignment.course.teacher_id != user_id:
        flash('只有教师可以评分。', 'warning')
        return redirect(url_for('dashboard.index'))
    
    # 处理兼容旧版的整体评分
    score = request.form.get('score')
    feedback = request.form.get('feedback')
    
    if score:
        try:
            AssignmentService.grade_assignment(
                student_id=student_id, 
                assignment_id=assignment_id, 
                score=float(score), 
                feedback=feedback
            )
            flash('评分已保存。', 'success')
        except ValueError as e:
            flash(str(e), 'danger')
    else:
        # 处理新的按问题评分
        questions = AssignmentService.get_assignment_questions(assignment_id)
        
        for question in questions:
            question_score = request.form.get(f'question_{question.id}_score')
            question_feedback = request.form.get(f'question_{question.id}_feedback')
            
            if question_score:
                try:
                    AssignmentService.grade_question_response(
                        student_id=student_id,
                        question_id=question.id,
                        score=float(question_score),
                        feedback=question_feedback
                    )
                except Exception as e:
                    flash(f'问题 {question.id} 评分失败: {str(e)}', 'danger')
        
        flash('所有问题的评分已保存。', 'success')
    
    return redirect(url_for('course.view_submission', assignment_id=assignment_id, student_id=student_id))

# 添加一个AJAX接口用于动态添加问题选项
@course_bp.route('/api/question_option_template', methods=['GET'])
def question_option_template():
    index = request.args.get('index', 0, type=int)
    question_index = request.args.get('question_index', 0, type=int)
    
    return render_template('course/_question_option.html', 
                          index=index,
                          question_index=question_index)

@course_bp.route('/<int:course_id>/knowledge_point/add', methods=['POST'])
def add_knowledge_point(course_id):
    """添加新的知识点到课程中"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    course = Course.get_by_id(course_id)
    
    # 验证权限
    if course.teacher_id != user_id:
        flash('只有课程教师可以添加知识点', 'warning')
        return redirect(url_for('course.view', course_id=course_id))
    
    name = request.form.get('name')
    description = request.form.get('description', '')
    parent_id = request.form.get('parent_id')
    
    # 如果父级ID为空字符串，则设为None
    if parent_id == '':
        parent_id = None
    elif parent_id:
        parent_id = int(parent_id)
    
    try:
        knowledge_point = KnowledgePointService.create_knowledge_point(
            name=name,
            course_id=course_id,
            description=description,
            parent_id=parent_id
        )
        flash(f'知识点 "{name}" 创建成功!', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    
    return redirect(url_for('course.view', course_id=course_id))

@course_bp.route('/<int:course_id>/knowledge_point/edit', methods=['POST'])
def edit_knowledge_point(course_id):
    """编辑课程中的知识点"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    course = Course.get_by_id(course_id)
    
    # 验证权限
    if course.teacher_id != user_id:
        flash('只有课程教师可以编辑知识点', 'warning')
        return redirect(url_for('course.view', course_id=course_id))
    
    knowledge_point_id = int(request.form.get('knowledge_point_id'))
    name = request.form.get('name')
    description = request.form.get('description', '')
    parent_id = request.form.get('parent_id')
    
    # 如果父级ID为空字符串，则设为None
    if parent_id == '':
        parent_id = None
    elif parent_id:
        parent_id = int(parent_id)
    
    try:
        # 获取知识点实例
        knowledge_point = KnowledgePointService.get_knowledge_point(knowledge_point_id)
        
        # 检查知识点是否属于当前课程
        if knowledge_point.course_id != course_id:
            raise ValueError('该知识点不属于当前课程')
        
        # 防止循环引用
        if parent_id and parent_id == knowledge_point_id:
            raise ValueError('知识点不能以自己作为父级')
        
        # 更新知识点
        knowledge_point.name = name
        knowledge_point.description = description
        knowledge_point.parent_id = parent_id
        knowledge_point.save()
        
        flash(f'知识点 "{name}" 更新成功!', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    
    return redirect(url_for('course.view', course_id=course_id))

@course_bp.route('/<int:course_id>/knowledge_point/delete', methods=['POST'])
def delete_knowledge_point(course_id):
    """删除课程中的知识点"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    course = Course.get_by_id(course_id)
    
    # 验证权限
    if course.teacher_id != user_id:
        flash('只有课程教师可以删除知识点', 'warning')
        return redirect(url_for('course.view', course_id=course_id))
    
    knowledge_point_id = int(request.form.get('knowledge_point_id'))
    
    try:
        # 获取知识点实例
        from app.models.learning_data import KnowledgePoint
        knowledge_point = KnowledgePointService.get_knowledge_point(knowledge_point_id)
        
        # 检查知识点是否属于当前课程
        if knowledge_point.course_id != course_id:
            raise ValueError('该知识点不属于当前课程')
        
        # 检查是否有子知识点
        children = KnowledgePoint.select().where(KnowledgePoint.parent_id == knowledge_point_id)
        if children.count() > 0:
            raise ValueError('该知识点有子知识点，请先删除或重新分配子知识点')
        
        # 保存名称以供通知
        kp_name = knowledge_point.name
        
        # 删除知识点
        knowledge_point.delete_instance()
        
        flash(f'知识点 "{kp_name}" 已删除', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    
    return redirect(url_for('course.view', course_id=course_id))

@course_bp.route('/assignment/<int:assignment_id>/knowledge_points', methods=['GET', 'POST'])
def assignment_knowledge_points(assignment_id):
    """管理作业关联的知识点"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    from app.models.assignment import Assignment
    
    assignment = Assignment.get_by_id(assignment_id)
    course_id = assignment.course_id
    user_id = session['user_id']
    
    # 验证权限
    if assignment.course.teacher_id != user_id:
        flash('只有课程教师可以管理作业知识点', 'warning')
        return redirect(url_for('course.view_assignment', assignment_id=assignment_id))
    
    if request.method == 'POST':
        # 获取提交的知识点ID列表
        knowledge_point_ids = request.form.getlist('knowledge_point_ids', type=int)
        
        # 获取权重
        weights = {}
        for kp_id in knowledge_point_ids:
            weight = request.form.get(f'weight_{kp_id}', 1.0, type=float)
            weights[kp_id] = weight
        
        try:
            # 清除旧的关联并添加新的
            from app.models.learning_data import AssignmentKnowledgePoint
            AssignmentKnowledgePoint.delete().where(
                AssignmentKnowledgePoint.assignment_id == assignment_id
            ).execute()
            
            if knowledge_point_ids:
                KnowledgePointService.add_knowledge_points_to_assignment(
                    assignment_id, knowledge_point_ids, weights
                )
            
            flash('作业知识点关联已更新', 'success')
        except ValueError as e:
            flash(str(e), 'danger')
        
        return redirect(url_for('course.view_assignment', assignment_id=assignment_id))
    
    # 获取课程所有知识点
    course_knowledge_points = KnowledgePointService.get_course_knowledge_points(course_id)
    
    # 获取作业已关联的知识点
    assignment_knowledge_points = KnowledgePointService.get_assignment_knowledge_points(assignment_id)
    
    return render_template('course/assignment_knowledge_points.html',
                          assignment=assignment,
                          course_knowledge_points=course_knowledge_points,
                          assignment_knowledge_points=assignment_knowledge_points)
