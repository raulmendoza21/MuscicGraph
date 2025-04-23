from src.db.mongodb_connection import get_mongo_database

db = get_mongo_database()

# Verifica que el usuario exista
print("📌 Usuarios:")
for user in db["users"].find():
    print("-", user['spotify_id'])

# Verifica que tenga canciones
print("\n🎵 Tracks de Yain:")
for track in db["top_tracks"].find({"user_spotify_id": "czgui137rykvesta5kinfxqk4"}):
    print("-", track['name'])

# Verifica que tenga playlists
print("\n📂 Playlists de Yain:")
for pl in db["playlists"].find({"user_spotify_id": "czgui137rykvesta5kinfxqk4"}):
    print("-", pl['name'])