from dotenv import load_dotenv
from pymongo import MongoClient
from collections import Counter, defaultdict
import os

# Eliminamos llamadas duplicadas a load_dotenv()
mongo_client = MongoClient(os.getenv("MONGODB_URI"))
db = mongo_client[os.getenv("MONGODB_DATABASE", "musicgraph")]

def analizar_perfil_usuario(user_id):
    tracks = list(db["top_tracks"].find({"user_spotify_id": user_id, "source": "top_tracks"}))
    if not tracks:
        return {
            "mensaje": "No se encontraron datos para este usuario.",
            "generos_principales": [],
            "perfil": "desconocido"
        }

    genero_counter = Counter()
    artista_counter = Counter()
    artista_nombres = {}
    popularidades = []

    for track in tracks:
        popularidades.append(track.get("popularity", 50))
        for artist in track.get("artists", []):
            artista_id = artist["spotify_id"]
            artista_counter[artista_id] += 1
            artista_nombres[artista_id] = artist["name"]
            genero_counter.update(artist.get("genres", []))

    total_generos = sum(genero_counter.values())
    generos_principales = genero_counter.most_common(5)
    generos_resumen = [
        {"genero": g, "porcentaje": round((c / total_generos) * 100, 1)}
        for g, c in generos_principales
    ]

    artista_top_id = artista_counter.most_common(1)[0][0]
    artista_top = artista_nombres.get(artista_top_id, "Desconocido")
    popularidad_promedio = round(sum(popularidades) / len(popularidades), 1)
    total_generos_distintos = len(genero_counter)

    perfil = "desconocido"
    if total_generos_distintos <= 2:
        perfil = "especialista"
    elif total_generos_distintos >= 8 and popularidad_promedio < 60:
        perfil = "explorador"
    elif "pop" in genero_counter or "latin" in genero_counter:
        perfil = "mainstream"
    elif popularidad_promedio < 40:
        perfil = "descubridor"
    else:
        perfil = "variado"

    return {
        "generos_principales": generos_resumen,
        "perfil": perfil,
        "mensaje": None,
        "extra": {
            "artista_top": artista_top,
            "popularidad_media": popularidad_promedio,
            "generos_distintos": total_generos_distintos
        }
    }

def usuario_existe(user_id: str) -> bool:
    db = mongo_client[os.getenv("MONGODB_DATABASE", "musicgraph")]
    return db["top_tracks"].count_documents({"user_spotify_id": user_id}) > 0