from flask import *
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.course_service import CourseService
from app.services.user_service import UserService
from app.models.user import User

from app.ext import cache

search_bp = Blueprint('search', __name__, url_prefix='/search')

@search_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    query = request.args.get('q', '')
    course_id = request.args.get('course_id')
    
    if course_id:
        try:
            course_id = int(course_id)
        except:
            course_id = None
    
    results = []
    if query:
        results = KnowledgeBaseService.search_knowledge(query, course_id)
    
    # 获取用户课程，用于筛选
    user_id = session['user_id']
    user = User.get_by_id(user_id)
    
    if UserService.has_role(user, 'teacher'):
        courses = CourseService.get_courses_by_teacher(user_id)
    else:
        courses = CourseService.get_courses_by_student(user_id)
    
    return render_template('search/index.html',
                         query=query,
                         results=results,
                         courses=courses,
                         selected_course_id=course_id)

@search_bp.route('/api/search')
#@cache.cached(timeout=300, query_string=True)
def api_search():
    """API端点, 用于AJAX搜索请求"""
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    query = request.args.get('q', '')
    course_id = request.args.get('course_id')
    limit = int(request.args.get('limit', 5))
    
    if course_id:
        try:
            course_id = int(course_id)
        except:
            course_id = None
    
    results = []
    if query:
        results = KnowledgeBaseService.search_knowledge(query, course_id, limit)
        
    # 将结果转换为简单的JSON结构
    simplified_results = []
    for result in results:
        simplified_results.append({
            "id": result["id"],
            "title": result["title"],
            "content": result["content"],
            "category": result["category"],
            "tags": result["tags"]
        })
    
    return jsonify({"results": simplified_results})

@search_bp.route('/manage')
def manage_knowledge():
    """管理知识库条目"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    user = User.get_by_id(user_id)
    
    # 只有教师和管理员可以管理知识库
    if not (UserService.has_role(user, 'teacher') or UserService.has_role(user, 'admin')):
        flash('您没有权限管理知识库。', 'warning')
        return redirect(url_for('search.index'))
    
    from app.models.knowledge_base import KnowledgeBase
    from app.models.course import Course
    
    if UserService.has_role(user, 'admin'):
        # 管理员可以看到所有条目
        entries = KnowledgeBase.select().prefetch(Course)
    else:
        # 教师只能看到自己课程的条目
        courses = CourseService.get_courses_by_teacher(user_id)
        course_ids = [course.id for course in courses]
        
        entries = KnowledgeBase.select().where(
            (KnowledgeBase.course_id.in_(course_ids)) |
            (KnowledgeBase.course_id.is_null())
        ).prefetch(Course)
    
    return render_template('search/manage.html', entries=entries)

@search_bp.route('/add', methods=['GET', 'POST'])
def add_knowledge():
    """添加知识库条目"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    user = User.get_by_id(user_id)
    
    # 只有教师和管理员可以添加知识库条目
    if not (UserService.has_role(user, 'teacher') or UserService.has_role(user, 'admin')):
        flash('您没有权限添加知识库条目。', 'warning')
        return redirect(url_for('search.index'))
    
    # 获取教师的课程，用于关联
    if UserService.has_role(user, 'teacher'):
        courses = CourseService.get_courses_by_teacher(user_id)
    else:
        from app.models.course import Course
        courses = Course.select()
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        course_id = request.form.get('course_id')
        category = request.form.get('category')
        tags = request.form.get('tags', '').split(',')
        
        if not course_id:
            course_id = None
            
        # 清理标签
        tags = [tag.strip() for tag in tags if tag.strip()]
        
        try:
            KnowledgeBaseService.add_knowledge(
                title=title,
                content=content,
                course_id=course_id,
                category=category,
                tags=tags
            )
            flash('知识条目已添加。', 'success')
            return redirect(url_for('search.manage_knowledge'))
        except Exception as e:
            flash(f'添加失败: {str(e)}', 'danger')
    
    return render_template('search/add_knowledge.html', courses=courses)

@search_bp.route('/edit/<int:knowledge_id>', methods=['GET', 'POST'])
def edit_knowledge(knowledge_id):
    """编辑知识库条目"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    user = User.get_by_id(user_id)
    
    # 权限检查
    if not (UserService.has_role(user, 'teacher') or UserService.has_role(user, 'admin')):
        flash('您没有权限编辑知识库条目。', 'warning')
        return redirect(url_for('search.index'))
    
    from app.models.knowledge_base import KnowledgeBase
    entry = KnowledgeBase.get_by_id(knowledge_id)
    
    # 获取课程列表
    if UserService.has_role(user, 'teacher'):
        courses = CourseService.get_courses_by_teacher(user_id)
        
        # 教师只能编辑自己课程的条目或无课程关联的条目
        if entry.course and entry.course.teacher_id != user_id:
            flash('您没有权限编辑该知识库条目。', 'warning')
            return redirect(url_for('search.manage_knowledge'))
    else:
        from app.models.course import Course
        courses = Course.select()
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        course_id = request.form.get('course_id')
        category = request.form.get('category')
        tags = request.form.get('tags', '').split(',')
        
        if not course_id:
            course_id = None
            
        # 清理标签
        tags = [tag.strip() for tag in tags if tag.strip()]
        
        try:
            KnowledgeBaseService.update_knowledge(
                knowledge_id=knowledge_id,
                title=title,
                content=content,
                category=category,
                tags=tags
            )
            
            # 更新课程关联
            entry.course_id = course_id
            entry.save()
            
            flash('知识条目已更新。', 'success')
            return redirect(url_for('search.manage_knowledge'))
        except Exception as e:
            flash(f'更新失败: {str(e)}', 'danger')
    
    return render_template('search/edit_knowledge.html', 
                         entry=entry, 
                         courses=courses,
                         tags=', '.join(entry.tags) if entry.tags else '')

@search_bp.route('/delete/<int:knowledge_id>', methods=['POST'])
def delete_knowledge(knowledge_id):
    """删除知识库条目"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    user = User.get_by_id(user_id)
    
    # 权限检查
    if not (UserService.has_role(user, 'teacher') or UserService.has_role(user, 'admin')):
        flash('您没有权限删除知识库条目。', 'warning')
        return redirect(url_for('search.index'))
    
    from app.models.knowledge_base import KnowledgeBase
    entry = KnowledgeBase.get_by_id(knowledge_id)
    
    # 教师只能删除自己课程的条目或无课程关联的条目
    if UserService.has_role(user, 'teacher') and entry.course and entry.course.teacher_id != user_id:
        flash('您没有权限删除该知识库条目。', 'warning')
        return redirect(url_for('search.manage_knowledge'))
    
    success = KnowledgeBaseService.delete_knowledge(knowledge_id)
    
    if success:
        flash('知识条目已删除。', 'success')
    else:
        flash('删除失败。', 'danger')
        
    return redirect(url_for('search.manage_knowledge'))
