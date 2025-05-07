from src.db.neo4j_connection import get_neo4j_driver
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGODB_URI")
MONGO_DB = os.getenv("MONGODB_DATABASE", "musicgraph")
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[MONGO_DB]

def get_recommendations(user_id, genero=None, limite=10):
    driver = get_neo4j_driver()
    recomendaciones = []

    query_similitud = """
    MATCH (u:User {spotify_id: $user_id})-[:MUSICAL_AFFINITY]->(vecino:User)
    MATCH (vecino)-[:LISTENS_TO]->(artista:Artist)
    WHERE NOT (u)-[:LISTENS_TO]->(artista)
    OPTIONAL MATCH (artista)-[:BELONGS_TO]->(g:Genre)
    WITH artista, COUNT(DISTINCT vecino) AS coincidencias,
         COLLECT(DISTINCT g.name) AS generos
    WHERE $genero IS NULL OR $genero IN generos
    RETURN artista.spotify_id AS spotify_id,
           artista.name AS nombre,
           coincidencias,
           generos
    ORDER BY coincidencias DESC
    LIMIT $limite
    """

    with driver.session() as session:
        results = session.run(query_similitud, user_id=user_id, genero=genero, limite=limite)
        recomendaciones = [
            {
                "spotify_id": r["spotify_id"],
                "nombre": r["nombre"],
                "coincidencias": r["coincidencias"],
                "popularidad": 0,  # default fallback
                "generos": r["generos"]
            }
            for r in results
        ]

    if len(recomendaciones) < limite:
        query_vecinos_fallback = """
        MATCH (u:User {spotify_id: $user_id})
        MATCH (otro:User)-[:LISTENS_TO]->(artista:Artist)
        WHERE NOT (u)-[:LISTENS_TO]->(artista)
        OPTIONAL MATCH (artista)-[:BELONGS_TO]->(g:Genre)
        WITH artista, COUNT(DISTINCT otro) AS coincidencias,
             COLLECT(DISTINCT g.name) AS generos
        WHERE $genero IS NULL OR $genero IN generos
        RETURN artista.spotify_id AS spotify_id,
               artista.name AS nombre,
               coincidencias,
               generos
        ORDER BY coincidencias DESC
        LIMIT $limite
        """

        with driver.session() as session:
            results = session.run(query_vecinos_fallback, user_id=user_id, genero=genero, limite=limite)
            recomendaciones.extend([
                {
                    "spotify_id": r["spotify_id"],
                    "nombre": r["nombre"],
                    "coincidencias": r["coincidencias"],
                    "popularidad": 0,
                    "generos": r["generos"]
                }
                for r in results
                if r["spotify_id"] not in {rec["spotify_id"] for rec in recomendaciones}
            ])

    if len(recomendaciones) < limite:
        faltan = limite - len(recomendaciones)
        populares = list(db["popular_tracks"].find(
            {
                "$or": [{"artists.genres": genero}] if genero else [{}]
            }
        ).sort("popularity", -1).limit(faltan))

        for p in populares:
            recomendaciones.append({
                "spotify_id": p["spotify_id"],
                "nombre": p["name"],
                "coincidencias": 0,
                "popularidad": p.get("popularity", 0),
                "generos": list({g for a in p["artists"] for g in a.get("genres", [])})
            })

    return recomendaciones

def get_explorador_recommendations(user_id, level=10):
    user_tracks = db["top_tracks"].find({"user_spotify_id": user_id})
    user_artist_ids = {t["spotify_id"] for t in user_tracks}

    pipeline = [
        {
            "$match": {
                "user_spotify_id": {"$ne": user_id},
                "spotify_id": {"$nin": list(user_artist_ids)}
            }
        },
        {
            "$group": {
                "_id": "$spotify_id",
                "nombre": {"$first": "$name"},
                "popularidad": {"$avg": "$popularity"},
                "generos": {"$addToSet": "$artists.genres"}
            }
        },
        {
            "$sort": {"popularidad": -1}
        },
        {
            "$limit": level
        }
    ]

    resultados = db["top_tracks"].aggregate(pipeline)

    recomendaciones = []
    for r in resultados:
        recomendaciones.append({
            "spotify_id": r["_id"],
            "nombre": r["nombre"],
            "coincidencias": 0,
            "popularidad": int(r.get("popularidad", 0)),
            "generos": list({g for sub in r.get("generos", []) for g in sub})
        })

    return recomendaciones

def recomendar_artistas_para_usuario(user_id, genero=None, limite=10):
    driver = get_neo4j_driver()

    query = """
    MATCH (u:User {spotify_id: $user_id})-[:MUSICAL_AFFINITY]->(vecino:User)
    MATCH (vecino)-[:LISTENS_TO]->(artista:Artist)
    WHERE NOT (u)-[:LISTENS_TO]->(artista)
    OPTIONAL MATCH (artista)-[:BELONGS_TO]->(g:Genre)
    WITH artista, COUNT(DISTINCT vecino) AS coincidencias,
         COLLECT(DISTINCT g.name) AS generos
    WHERE $genero IS NULL OR $genero IN generos
    RETURN artista.spotify_id AS spotify_id,
           artista.name AS nombre,
           coincidencias,
           generos
    ORDER BY coincidencias DESC
    LIMIT $limite
    """

    with driver.session() as session:
        results = session.run(query, user_id=user_id, genero=genero, limite=limite)
        recomendaciones = []
        for record in results:
            recomendaciones.append({
                "spotify_id": record["spotify_id"],
                "nombre": record["nombre"],
                "coincidencias": record["coincidencias"],
                "popularidad": 0,
                "generos": record["generos"]
            })
        return recomendaciones
