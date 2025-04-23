from src.db.mongodb_connection import get_mongo_database

def borrar_playlists_sin_usuario():
    db = get_mongo_database()
    result = db['playlists'].delete_many({'user_spotify_id': {'$exists': False}})
    print(f"🧹 Playlists sin 'user_spotify_id' eliminadas: {result.deleted_count}")

if __name__ == "__main__":
    borrar_playlists_sin_usuario()
