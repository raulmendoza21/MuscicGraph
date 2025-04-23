from src.db.mongodb_connection import get_mongo_database

db = get_mongo_database()
result = db['top_tracks'].delete_many({'user_spotify_id': {'$exists': False}})
print(f"🧹 Canciones eliminadas por falta de user_spotify_id: {result.deleted_count}")