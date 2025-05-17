# extensions
from flask_caching import Cache
#from playhouse.postgres_ext import PostgresqlExtDatabase
from playhouse.pool import PooledPostgresqlExtDatabase
from chromadb import PersistentClient
import os

#db = PostgresqlExtDatabase(None)
db = PooledPostgresqlExtDatabase(None)

chroma_client = None
knowledge_base_collection = None
cache = Cache()

def initialize_extensions():
    # initialize database
    db.init(os.getenv("DATABASE_NAME"),
            host=os.getenv("DATABASE_HOST"),
            user=os.getenv("DATABASE_USER"),
            password=os.getenv("DATABASE_PASSWORD"),
            port=os.getenv("DATABASE_PORT"),
            max_connections=9,          # 必须大于 Gunicorn 的 worker 数量
            stale_timeout=300,           # 空闲连接回收时间（秒）
            #autoconnect=False            # 推荐关闭自动连接
    )
    
    # initialize chroma
    global chroma_client
    chroma_client = PersistentClient(path=os.getenv("CHROMA_PERSIST_DIRECTORY"))
    global knowledge_base_collection
    knowledge_base_collection = chroma_client.get_or_create_collection("knowledge_base")
