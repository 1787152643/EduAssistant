from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from app.services.user_service import UserService
from app.ext import cache

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
@cache.cached(timeout=60, query_string=True)
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = UserService.authenticate_user(username, password)
        
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            flash('登录成功!', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('用户名或密码错误。', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        name = request.form.get('name')
        
        try:
            user = UserService.create_user(username, email, password, name, ['student'])
            flash('注册成功，请登录。', 'success')
            return redirect(url_for('auth.login'))
        except ValueError as e:
            flash(str(e), 'danger')
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('您已退出登录。', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        return
