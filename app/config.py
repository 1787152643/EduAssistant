import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    
    # 数据库配置
    DATABASE_NAME = os.environ.get('DATABASE_NAME') or 'eduassistant-v3'
    DATABASE_USER = os.environ.get('DATABASE_USER') or 'postgres'
    DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD') or 'rachel'
    DATABASE_HOST = os.environ.get('DATABASE_HOST') or 'localhost'
    DATABASE_PORT = int(os.environ.get('DATABASE_PORT') or 5432)
    
    # Chroma配置
    CHROMA_PERSIST_DIRECTORY = os.environ.get('CHROMA_PERSIST_DIRECTORY') or 'chroma_db'

    # Google搜索配置
    GOOGLE_SEARCH_API_KEY = os.environ.get('GOOGLE_SEARCH_API_KEY')
    GOOGLE_SEARCH_CX = os.environ.get('GOOGLE_SEARCH_CX')
    GOOGLE_SEARCH_PROXY = os.environ.get('GOOGLE_SEARCH_PROXY') or 'NO_PROXY'
    
    # 缓存配置
    CACHE_TYPE = os.environ.get('CACHE_TYPE') or 'SimpleCache'  # 默认使用SimpleCache
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT') or 300)  # 默认缓存5分钟
    CACHE_THRESHOLD = int(os.environ.get('CACHE_THRESHOLD') or 500)  # 最大项目数
    CACHE_KEY_PREFIX = os.environ.get('CACHE_KEY_PREFIX') or 'eduassistant_'