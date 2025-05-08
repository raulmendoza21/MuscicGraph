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

    # 🎯 Recomendaciones por afinidad
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
                "popularidad": 0,
                "generos": r["generos"],
                "origen": "afinidad"
            }
            for r in results
        ]

    # 🔁 Fallback por otros usuarios si no hay suficientes
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
                    "generos": r["generos"],
                    "origen": "otros usuarios"
                }
                for r in results
                if r["spotify_id"] not in {rec["spotify_id"] for rec in recomendaciones}
            ])

    # 📊 Fallback por popularidad (Mongo)
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
                "generos": list({g for a in p["artists"] for g in a.get("genres", [])}),
                "origen": "popularidad"
            })
        
        max_coinc = max([r["coincidencias"] for r in recomendaciones], default=1)
        max_pop = max([r.get("popularidad", 0) for r in recomendaciones], default=1)

        for r in recomendaciones:
            afinidad_norm = r["coincidencias"] / max_coinc if max_coinc > 0 else 0
            pop_norm = r.get("popularidad", 0) / 100  # popularidad va de 0 a 100
            diversidad = len(set(r.get("generos", []))) / 10  # hasta 10 géneros distintos

            r["score"] = round(0.6 * afinidad_norm + 0.3 * pop_norm + 0.1 * diversidad, 4)

        recomendaciones.sort(key=lambda r: r["score"], reverse=True)
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
            "generos": list({g for sub in r.get("generos", []) for g in sub}),
            "origen": "explorador"
        })

    return recomendaciones

def get_discovery_recommendations(user_id, limite=10):
    user_tracks = db["top_tracks"].find({"user_spotify_id": user_id})
    user_artist_ids = {t["spotify_id"] for t in user_tracks}

    pipeline = [
        {
            "$match": {
                "user_spotify_id": {"$ne": user_id},
                "spotify_id": {"$nin": list(user_artist_ids)},
                "popularity": {"$lt": 60}  # 🎯 menos conocidos
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
            "$limit": limite
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
            "generos": list({g for sub in r.get("generos", []) for g in sub}),
            "origen": "descubrimiento"
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
