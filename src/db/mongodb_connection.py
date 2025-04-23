import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def get_mongo_client():
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        raise ValueError("❌ No se encontró MONGODB_URI en el .env")
    return MongoClient(mongodb_uri)

def get_mongo_database():
    client = get_mongo_client()
    database_name = os.getenv("MONGODB_DATABASE", "musicgraph")
    return client[database_name]
