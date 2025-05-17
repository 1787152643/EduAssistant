from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from app.services.user_service import UserService
from app.models.user import User, Role, UserRole

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# 管理员访问权限检查装饰器
def admin_required(view_func):
    def wrapped_view(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        
        user = User.get_by_id(session['user_id'])
        if not UserService.has_role(user, 'admin'):
            flash('您没有管理员权限。', 'danger')
            return redirect(url_for('dashboard.index'))
            
        return view_func(*args, **kwargs)
    
    wrapped_view.__name__ = view_func.__name__
    return wrapped_view

@admin_bp.route('/')
@admin_required
def index():
    return render_template('admin/dashboard.html')

@admin_bp.route('/users')
@admin_required
def users():
    all_users = User.select().prefetch(UserRole.select().prefetch(Role))
    return render_template('admin/users.html', users=all_users)

@admin_bp.route('/users/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = User.get_by_id(user_id)
    roles = Role.select()
    user_roles = [ur.role.id for ur in user.roles]
    
    if request.method == 'POST':
        # 更新用户信息
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        user.name = request.form.get('name')
        user.is_active = 'is_active' in request.form
        user.save()
        
        # 更新角色
        UserRole.delete().where(UserRole.user == user).execute()
        for role_id in request.form.getlist('roles'):
            UserRole.create(user=user, role_id=role_id)
            
        flash('用户信息已更新。', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/edit_user.html', user=user, roles=roles, user_roles=user_roles)

@admin_bp.route('/roles')
@admin_required
def roles():
    all_roles = Role.select()
    return render_template('admin/roles.html', roles=all_roles)

@admin_bp.route('/roles/add', methods=['GET', 'POST'])
@admin_required
def add_role():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        if Role.select().where(Role.name == name).exists():
            flash(f"角色 '{name}' 已存在。", 'danger')
        else:
            Role.create(name=name, description=description)
            flash('角色已创建。', 'success')
            return redirect(url_for('admin.roles'))
    
    return render_template('admin/add_role.html')

@admin_bp.route('/initialize', methods=['GET', 'POST'])
def initialize_system():
    # 只有在没有任何角色定义时才允许初始化
    if Role.select().count() > 0:
        flash('系统已初始化，无法重新初始化。', 'warning')
        return redirect(url_for('admin.index'))
    
    if request.method == 'POST':
        # 创建基础角色
        roles = {
            'admin': '系统管理员',
            'teacher': '教师',
            'student': '学生'
        }
        
        for role_name, description in roles.items():
            Role.create(name=role_name, description=description)
            
        # 创建管理员账户
        admin_username = request.form.get('admin_username', 'root')
        admin_password = request.form.get('admin_password', '123456')
        admin_email = request.form.get('admin_email', 'admin@example.com')
        admin_name = request.form.get('admin_name', 'root')
        
        try:
            admin_user = UserService.create_user(
                username=admin_username,
                email=admin_email,
                password=admin_password,
                name=admin_name,
                role_names=['admin']
            )
            session['user_id'] = admin_user.id
            session['username'] = admin_user.username
            
            flash('系统初始化完成！已创建管理员账户。', 'success')
            return redirect(url_for('dashboard.index'))
        except ValueError as e:
            flash(str(e), 'danger')
    
    return render_template('admin/initialize.html')
