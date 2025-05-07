from src.db.mongodb_connection import get_mongo_collection
from datetime import datetime

def store_user_data(username, user_info, top_artists):
    collection = get_mongo_collection("usuarios")
    doc = {
        "username": username,
        "spotify_id": user_info['id'],
        "display_name": user_info.get('display_name'),
        "email": user_info.get('email', ''),
        "top_artists": top_artists,
        "joined_at": datetime.now().isoformat()
    }
    collection.update_one({"username": username}, {"$set": doc}, upsert=True)
