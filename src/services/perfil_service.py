# src/services/perfil_service.py
from pymongo import MongoClient
from collections import Counter
import os
from dotenv import load_dotenv

load_dotenv()

mongo_client = MongoClient(os.getenv("MONGODB_URI"))
db = mongo_client[os.getenv("MONGODB_DATABASE", "musicgraph")]

def analizar_perfil_usuario(user_id):
    tracks = list(db["top_tracks"].find({"user_spotify_id": user_id}))
    
    if not tracks:
        return {
            "mensaje": "No se encontraron datos para este usuario.",
            "generos_principales": [],
            "perfil": "desconocido"
        }

    genero_counter = Counter()

    for track in tracks:
        for artist in track.get("artists", []):
            genero_counter.update(artist.get("genres", []))

    total = sum(genero_counter.values())

    generos_principales = genero_counter.most_common(5)
    generos_resumen = [
        {"genero": g, "porcentaje": round((c / total) * 100, 1)}
        for g, c in generos_principales
    ]

    # Clasificación de perfil
    if len(generos_counter := genero_counter.keys()) <= 2:
        perfil = "especialista"
    elif len(generos_counter) >= 8:
        perfil = "explorador"
    elif "pop" in genero_counter or "latin" in genero_counter:
        perfil = "mainstream"
    else:
        perfil = "variado"

    return {
        "generos_principales": generos_resumen,
        "perfil": perfil,
        "mensaje": None
    }
