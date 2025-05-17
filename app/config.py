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

    # cache
    CACHE_TYPE = 'RedisCache'
    CACHE_REDIS_HOST = 'localhost'
    CACHE_REDIS_PORT = 6379
    CACHE_REDIS_DB = 0
    CACHE_DEFAULT_TIMEOUT = 60
