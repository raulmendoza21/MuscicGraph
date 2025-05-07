# src/graph/graph_builder_full.py
from src.db.mongodb_connection import get_mongo_database
from src.db.neo4j_connection import get_neo4j_driver
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')



def resetear_grafo():
    driver = get_neo4j_driver()
    with driver.session() as session:
        result = session.run("MATCH (n) DETACH DELETE n")
        print("🧨 Todos los nodos y relaciones han sido eliminados.")

def construir_grafo_completo():
    db = get_mongo_database()
    driver = get_neo4j_driver()

    users = list(db["users"].find())
    tracks = list(db["top_tracks"].find())

    with driver.session() as session:
        logging.info("🚧 Eliminando grafo anterior...")
        session.run("MATCH (n) DETACH DELETE n")

        logging.info("🔧 Creando nodos de usuarios...")
        for user in users:
            session.run("""
                MERGE (u:User {spotify_id: $id})
                SET u.display_name = $name
            """, id=user["spotify_id"], name=user["display_name"])

        logging.info("🎵 Creando nodos de artistas y relaciones LISTENS_TO...")
        for track in tracks:
            user_id = track.get("user_spotify_id")
            if not user_id or "artists" not in track:
                continue

            for artist in track["artists"]:
                session.run("""
                    MERGE (a:Artist {spotify_id: $artist_id})
                    SET a.name = $artist_name
                """, artist_id=artist["spotify_id"], artist_name=artist["name"])

                session.run("""
                    MATCH (u:User {spotify_id: $user_id})
                    MATCH (a:Artist {spotify_id: $artist_id})
                    MERGE (u)-[:LISTENS_TO]->(a)
                """, user_id=user_id, artist_id=artist["spotify_id"])

        logging.info("🤝 Creando relaciones COLLABORATED_WITH entre artistas...")
        for track in tracks:
            artists = track.get("artists", [])
            for i in range(len(artists)):
                for j in range(i + 1, len(artists)):
                    session.run("""
                        MATCH (a1:Artist {spotify_id: $id1}), (a2:Artist {spotify_id: $id2})
                        MERGE (a1)-[:COLLABORATED_WITH]->(a2)
                        MERGE (a2)-[:COLLABORATED_WITH]->(a1)
                    """, id1=artists[i]["spotify_id"], id2=artists[j]["spotify_id"])

        logging.info("🏷️ Creando nodos Genre y relaciones BELONGS_TO...")
        genre_mapping = defaultdict(list)
        for track in tracks:
            for artist in track.get("artists", []):
                for genre in artist.get("genres", []):
                    genre_mapping[genre].append(artist["spotify_id"])

        for genre, artist_ids in genre_mapping.items():
            session.run("MERGE (:Genre {name: $genre})", genre=genre)
            for artist_id in artist_ids:
                session.run("""
                    MATCH (a:Artist {spotify_id: $artist_id}), (g:Genre {name: $genre})
                    MERGE (a)-[:BELONGS_TO]->(g)
                """, artist_id=artist_id, genre=genre)

        logging.info("👥 Calculando afinidad musical entre usuarios...")
        for i, u1 in enumerate(users):
            for u2 in users[i + 1:]:
                u1_artists, u2_artists = set(), set()
                u1_genres, u2_genres = set(), set()

                for track in tracks:
                    if "artists" not in track:
                        continue
                    for artist in track["artists"]:
                        if track.get("user_spotify_id") == u1["spotify_id"]:
                            u1_artists.add(artist["spotify_id"])
                            u1_genres.update(artist.get("genres", []))
                        elif track.get("user_spotify_id") == u2["spotify_id"]:
                            u2_artists.add(artist["spotify_id"])
                            u2_genres.update(artist.get("genres", []))

                if not u1_artists and not u1_genres:
                    continue

                sim_artists = len(u1_artists & u2_artists) / len(u1_artists | u2_artists) if u1_artists | u2_artists else 0
                sim_genres = len(u1_genres & u2_genres) / len(u1_genres | u2_genres) if u1_genres | u2_genres else 0
                total_score = round(0.6 * sim_artists + 0.4 * sim_genres, 4)

                if total_score > 0:
                    session.run("""
                        MATCH (u1:User {spotify_id: $id1}), (u2:User {spotify_id: $id2})
                        MERGE (u1)-[r1:MUSICAL_AFFINITY]->(u2)
                        SET r1.score = $score
                        MERGE (u2)-[r2:MUSICAL_AFFINITY]->(u1)
                        SET r2.score = $score
                    """, id1=u1["spotify_id"], id2=u2["spotify_id"], score=total_score)

        logging.info("✅ Grafo completo construido exitosamente.")

if __name__ == "__main__":
    resetear_grafo()
    construir_grafo_completo()
