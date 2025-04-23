from src.db.mongodb_connection import get_mongo_database

from pprint import pprint

def revisar_datos_mongodb():
    db = get_mongo_database()

    print("👤 Usuario:")
    user = db["users"].find_one()
    pprint(user)

    print("\n🎵 Canciones (top_tracks):")
    for track in db["top_tracks"].find().limit(3):
        pprint(track)

    print("\n📂 Playlists:")
    for playlist in db["playlists"].find().limit(2):
        pprint(playlist)

if __name__ == "__main__":
    revisar_datos_mongodb()
