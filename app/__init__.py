from flask import Flask
from app.ext import initialize_extensions, cache
from app.config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 初始化扩展 (postgres, chroma)
    initialize_extensions()
    
    # 初始化缓存
    cache.init_app(app)
    
    # 注册蓝图
    from app.views.auth import auth_bp
    from app.views.dashboard import dashboard_bp
    from app.views.admin import admin_bp
    from app.views.analytics import analytics_bp
    from app.views.course import course_bp
    from app.views.search import search_bp
    from app.views.ai_assistant import ai_assistant_bp
    from app.views.recommend import recommend_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(course_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(ai_assistant_bp)
    app.register_blueprint(recommend_bp)
    
    return app