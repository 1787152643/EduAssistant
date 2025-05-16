# extensions

from playhouse.postgres_ext import PostgresqlExtDatabase
from chromadb import PersistentClient
from flask_caching import Cache
import os

db = PostgresqlExtDatabase(None)
cache = Cache()

chroma_client = None
knowledge_base_collection = None

def initialize_extensions():
    # initialize database
    db.init(os.getenv("DATABASE_NAME"),
            host=os.getenv("DATABASE_HOST"),
            user=os.getenv("DATABASE_USER"),
            password=os.getenv("DATABASE_PASSWORD"),
            port=os.getenv("DATABASE_PORT"))
    
    # initialize chroma
    global chroma_client
    chroma_client = PersistentClient(path=os.getenv("CHROMA_PERSIST_DIRECTORY"))
    global knowledge_base_collection
    knowledge_base_collection = chroma_client.get_or_create_collection("knowledge_base")