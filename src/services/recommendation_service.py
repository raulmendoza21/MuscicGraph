from src.db.neo4j_connection import get_neo4j_driver
from pymongo import MongoClient
import os

MONGO_URI = os.getenv("MONGODB_URI")
MONGO_DB = os.getenv("MONGODB_DATABASE", "musicgraph")
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[MONGO_DB]

def get_recommendations(user_id, genero=None, limite=10):
    driver = get_neo4j_driver()
    recomendaciones = []
    recomendados_ids = set()

    query_similitud = """
    MATCH (u:User {spotify_id: $user_id})-[a:MUSICAL_AFFINITY]->(vecino:User)
    MATCH (vecino)-[:LISTENS_TO]->(artista:Artist)
    WHERE NOT (u)-[:LISTENS_TO]->(artista)
    OPTIONAL MATCH (artista)-[:BELONGS_TO]->(g:Genre)
    WITH artista, SUM(a.score) AS afinidad_total,
         COLLECT(DISTINCT g.name) AS generos
    WHERE afinidad_total >= 0.3
      AND ($genero IS NULL OR $genero IN generos)
    RETURN artista.spotify_id AS spotify_id,
           artista.name AS nombre,
           afinidad_total,
           generos
    ORDER BY afinidad_total DESC
    LIMIT $limite
    """

    with driver.session() as session:
        results = session.run(query_similitud, user_id=user_id, genero=genero, limite=limite)
        for r in results:
            recomendaciones.append({
                "spotify_id": r["spotify_id"],
                "nombre": r["nombre"],
                "coincidencias": round(r["afinidad_total"], 2),
                "popularidad": 0,
                "generos": r["generos"],
                "origen": "afinidad"
            })
            recomendados_ids.add(r["spotify_id"])

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
            for r in results:
                if r["spotify_id"] not in recomendados_ids:
                    recomendaciones.append({
                        "spotify_id": r["spotify_id"],
                        "nombre": r["nombre"],
                        "coincidencias": r["coincidencias"],
                        "popularidad": 0,
                        "generos": r["generos"],
                        "origen": "otros usuarios"
                    })
                    recomendados_ids.add(r["spotify_id"])

    if len(recomendaciones) < limite:
        faltan = limite - len(recomendaciones)
        user_tracks = db["top_tracks"].find({"user_spotify_id": user_id})
        user_artist_ids = {a["spotify_id"] for t in user_tracks for a in t.get("artists", [])}

        pipeline = [
            {"$match": {
                "popularity": {"$gte": 40},
                "artists.spotify_id": {"$nin": list(user_artist_ids)},
                **({"artists.genres": genero} if genero else {})
            }},
            {"$group": {
                "_id": "$spotify_id",
                "nombre": {"$first": "$name"},
                "popularidad": {"$avg": "$popularity"},
                "generos": {"$addToSet": "$artists.genres"},
                "usuarios": {"$addToSet": "$user_spotify_id"}
            }},
            {"$project": {
                "nombre": 1,
                "popularidad": 1,
                "generos": 1,
                "num_usuarios": {"$size": "$usuarios"}
            }},
            {"$sort": {"num_usuarios": -1, "popularidad": -1}},
            {"$limit": faltan * 2}  # más margen por si hay duplicados
        ]

        populares = db["top_tracks"].aggregate(pipeline)
        for p in populares:
            if p["_id"] not in recomendados_ids:
                recomendaciones.append({
                    "spotify_id": p["_id"],
                    "nombre": p["nombre"],
                    "coincidencias": 0,
                    "popularidad": int(p["popularidad"]),
                    "generos": list({g for sub in p["generos"] for g in sub}),
                    "origen": "popularidad"
                })
                recomendados_ids.add(p["_id"])
            if len(recomendaciones) >= limite:
                break

    max_coinc = max([r["coincidencias"] for r in recomendaciones if r["coincidencias"] > 0], default=1)
    max_pop = max([r.get("popularidad", 0) for r in recomendaciones], default=1)

    for r in recomendaciones:
        afinidad_norm = r["coincidencias"] / max_coinc if max_coinc > 0 else 0
        pop_norm = r.get("popularidad", 0) / 100
        diversidad = len(set(r.get("generos", []))) / 10
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
