import os
from pymongo import MongoClient
from neo4j import GraphDatabase
from dotenv import load_dotenv
from collections import defaultdict
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# Cargar .env
load_dotenv()

# Conexión MongoDB
mongo_uri = os.getenv("MONGODB_URI")
mongo_db_name = os.getenv("MONGODB_DATABASE", "musicgraph")
mongo_client = MongoClient(mongo_uri)
db = mongo_client[mongo_db_name]

# Conexión Neo4j
neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
neo4j_user = os.getenv("NEO4J_USER", "neo4j")
neo4j_pass = os.getenv("NEO4J_PASSWORD", "password")
neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_pass))


# ========== FUNCIÓN 1: GÉNEROS ==========
def create_genre_relationships(session):
    genre_mapping = defaultdict(list)
    artists_collection = db.top_tracks

    for track in artists_collection.find():
        for artist in track.get('artists', []):
            for genre in artist.get('genres', []):
                genre_mapping[genre].append(artist['spotify_id'])

    for genre, artist_ids in genre_mapping.items():
        session.run("MERGE (:Genre {name: $genre})", genre=genre)
        for artist_id in artist_ids:
            session.run("""
                MATCH (a:Artist {spotify_id: $artist_id}), (g:Genre {name: $genre})
                MERGE (a)-[:BELONGS_TO]->(g)
            """, artist_id=artist_id, genre=genre)

    logging.info("🎵 Relaciones de género creadas.")


# ========== FUNCIÓN 2: SIMILITUD ENTRE USUARIOS ==========
def create_user_similarity(session):
    users = list(db.users.find())
    tracks = list(db.top_tracks.find())

    for i, user1 in enumerate(users):
        for user2 in users[i + 1:]:
            u1_artists = set()
            u2_artists = set()

            for track in tracks:
                if 'artists' in track:
                    for artist in track['artists']:
                        if track.get('user_spotify_id') == user1['spotify_id']:
                            u1_artists.add(artist['spotify_id'])
                        if track.get('user_spotify_id') == user2['spotify_id']:
                            u2_artists.add(artist['spotify_id'])

            intersection = len(u1_artists & u2_artists)
            union = len(u1_artists | u2_artists)
            similarity = intersection / union if union > 0 else 0

            if similarity > 0.3:
                session.run("""
                    MATCH (u1:User {spotify_id: $id1}), (u2:User {spotify_id: $id2})
                    MERGE (u1)-[:MUSICAL_AFFINITY {score: $score}]->(u2)
                    MERGE (u2)-[:MUSICAL_AFFINITY {score: $score}]->(u1)
                """, id1=user1['spotify_id'], id2=user2['spotify_id'], score=similarity)

    logging.info("👥 Relaciones de afinidad musical creadas.")


# ========== FUNCIÓN 3: COLABORACIÓN ENTRE ARTISTAS ==========
def create_artist_collaborations(session):
    tracks = db.top_tracks.find()

    for track in tracks:
        artists = track.get('artists', [])
        if len(artists) > 1:
            for i in range(len(artists)):
                for j in range(i + 1, len(artists)):
                    session.run("""
                        MATCH (a1:Artist {spotify_id: $id1}), (a2:Artist {spotify_id: $id2})
                        MERGE (a1)-[:COLLABORATED_WITH]->(a2)
                        MERGE (a2)-[:COLLABORATED_WITH]->(a1)
                    """, id1=artists[i]['spotify_id'], id2=artists[j]['spotify_id'])

    logging.info("🤝 Relaciones de colaboración entre artistas creadas.")


# ========== EJECUCIÓN PRINCIPAL ==========
def create_advanced_relationships():
    try:
        with neo4j_driver.session() as session:
            logging.info("🚀 Iniciando creación de relaciones avanzadas...")
            create_genre_relationships(session)
            create_user_similarity(session)
            create_artist_collaborations(session)
            logging.info("✅ Relaciones avanzadas creadas exitosamente.")
    except Exception as e:
        logging.error(f"❌ Error al crear relaciones avanzadas: {e}")

if __name__ == "__main__":
    create_advanced_relationships()
