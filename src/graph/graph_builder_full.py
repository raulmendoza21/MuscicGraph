from src.db.mongodb_connection import get_mongo_database
from src.db.neo4j_connection import get_neo4j_driver
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def resetear_grafo():
    driver = get_neo4j_driver()
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        print("🧨 Todos los nodos y relaciones han sido eliminados.")

def eliminar_grafo_anterior(session):
    logging.info("🚧 Eliminando grafo anterior...")
    session.run("MATCH (n) DETACH DELETE n")

def crear_nodos_usuarios(session, users):
    logging.info("🔧 Creando nodos de usuarios...")
    for user in users:
        session.run("""
            MERGE (u:User {spotify_id: $id})
            SET u.display_name = $name
        """, id=user["spotify_id"], name=user["display_name"])

def crear_nodos_y_relaciones_artistas(session, tracks):
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

def crear_relaciones_colaboracion(session, tracks):
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

def crear_nodos_y_relaciones_generos(session, tracks):
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

def calcular_afinidad_usuarios(session, users, tracks):
    logging.info("👥 Calculando afinidad musical entre usuarios...")
    top_tracks = [t for t in tracks if t.get("source") == "top_tracks"]

    datos_usuario = defaultdict(lambda: {"artistas": set(), "generos": set()})
    for track in top_tracks:
        user_id = track.get("user_spotify_id")
        for artist in track.get("artists", []):
            datos_usuario[user_id]["artistas"].add(artist["spotify_id"])
            datos_usuario[user_id]["generos"].update(artist.get("genres", []))

    for i, u1 in enumerate(users):
        id1 = u1["spotify_id"]
        for u2 in users[i + 1:]:
            id2 = u2["spotify_id"]

            u1_artistas = datos_usuario[id1]["artistas"]
            u2_artistas = datos_usuario[id2]["artistas"]
            u1_generos = datos_usuario[id1]["generos"]
            u2_generos = datos_usuario[id2]["generos"]

            if len(u1_artistas) < 5 or len(u2_artistas) < 5:
                continue

            inter_artistas = len(u1_artistas & u2_artistas)
            union_artistas = len(u1_artistas | u2_artistas)
            sim_artistas = inter_artistas / union_artistas if union_artistas else 0

            inter_generos = len(u1_generos & u2_generos)
            union_generos = len(u1_generos | u2_generos)
            sim_generos = inter_generos / union_generos if union_generos else 0

            diversidad_1 = len(u1_generos)
            diversidad_2 = len(u2_generos)
            penalizacion_mainstream = 0.0
            if "pop" in u1_generos and "pop" in u2_generos:
                penalizacion_mainstream = 0.1

            total_score = 0.6 * sim_artistas + 0.4 * sim_generos
            total_score = total_score * (1 - penalizacion_mainstream)
            total_score = round(total_score, 4)

            
            if inter_artistas < 1 and inter_generos < 1:
                continue

            if total_score > 0:
                session.run("""
                    MATCH (u1:User {spotify_id: $id1}), (u2:User {spotify_id: $id2})
                    MERGE (u1)-[r1:MUSICAL_AFFINITY]->(u2)
                    SET r1.score = $score
                    MERGE (u2)-[r2:MUSICAL_AFFINITY]->(u1)
                    SET r2.score = $score
                """, id1=id1, id2=id2, score=total_score)

def construir_grafo_completo():
    db = get_mongo_database()
    driver = get_neo4j_driver()
    users = list(db["users"].find())
    tracks = list(db["top_tracks"].find())

    with driver.session() as session:
        eliminar_grafo_anterior(session)
        crear_nodos_usuarios(session, users)
        crear_nodos_y_relaciones_artistas(session, tracks)
        crear_relaciones_colaboracion(session, tracks)
        crear_nodos_y_relaciones_generos(session, tracks)
        calcular_afinidad_usuarios(session, users, tracks)

    logging.info("✅ Grafo completo construido exitosamente.")

if __name__ == "__main__":
    resetear_grafo()
    construir_grafo_completo()
