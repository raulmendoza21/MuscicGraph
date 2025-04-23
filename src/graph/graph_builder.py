from src.db.mongodb_connection import get_mongo_database
from src.db.neo4j_connection import get_neo4j_driver
from collections import defaultdict

def construir_grafo():
    db = get_mongo_database()
    driver = get_neo4j_driver()

    users = list(db['users'].find())
    tracks = list(db['top_tracks'].find())  # Incluye tanto de top_tracks como playlists

    print("🎯 Creando nodos y relaciones en Neo4j...")

    with driver.session() as session:
        # Nodos de usuarios
        for user in users:
            session.run("""
                MERGE (u:User {spotify_id: $id})
                SET u.display_name = $name
            """, id=user['spotify_id'], name=user['display_name'])

        # Nodos de artistas y relaciones con usuarios
        for track in tracks:
            user_id = track.get('user_spotify_id')
            if not user_id or 'artists' not in track:
                continue

            for artist in track['artists']:
                session.run("""
                    MERGE (a:Artist {spotify_id: $artist_id})
                    SET a.name = $artist_name
                """, artist_id=artist['spotify_id'], artist_name=artist['name'])

                session.run("""
                    MATCH (u:User {spotify_id: $user_id})
                    MATCH (a:Artist {spotify_id: $artist_id})
                    MERGE (u)-[:LISTENS_TO]->(a)
                """, user_id=user_id, artist_id=artist['spotify_id'])

        # Colaboraciones entre artistas (tracks con múltiples artistas)
        for track in tracks:
            artists = track.get('artists', [])
            if len(artists) > 1:
                for i in range(len(artists)):
                    for j in range(i + 1, len(artists)):
                        session.run("""
                            MATCH (a1:Artist {spotify_id: $a1})
                            MATCH (a2:Artist {spotify_id: $a2})
                            MERGE (a1)-[:COLLABORATED_WITH]->(a2)
                            MERGE (a2)-[:COLLABORATED_WITH]->(a1)
                        """, a1=artists[i]['spotify_id'], a2=artists[j]['spotify_id'])

        # Afinidad musical entre usuarios (según artistas en común)
        print("🔍 Calculando afinidad musical...")
        for i, u1 in enumerate(users):
            for u2 in users[i+1:]:
                u1_artists = set(
                    artist['spotify_id']
                    for track in tracks if track['user_spotify_id'] == u1['spotify_id']
                    for artist in track.get('artists', [])
                )
                u2_artists = set(
                    artist['spotify_id']
                    for track in tracks if track['user_spotify_id'] == u2['spotify_id']
                    for artist in track.get('artists', [])
                )
                intersection = u1_artists.intersection(u2_artists)
                union = u1_artists.union(u2_artists)
                similarity = len(intersection) / len(union) if union else 0
                print(f"🔗 Afinidad entre {u1['display_name']} y {u2['display_name']}: {similarity:.2f} ({len(intersection)} artistas en común)")

                if similarity >= 0.00 and u1['spotify_id'] != u2['spotify_id']:
                    session.run("""
                        MERGE (u1:User {spotify_id: $id1})
                        MERGE (u2:User {spotify_id: $id2})
                        MERGE (u1)-[r:MUSICAL_AFFINITY]->(u2)
                        SET r.score = $score
                    """, id1=u1['spotify_id'], id2=u2['spotify_id'], score=similarity)

        print("✅ Grafo generado correctamente en Neo4j.")

if __name__ == "__main__":
    construir_grafo()
