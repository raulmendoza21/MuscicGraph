# src/api/recommend.py
from flask import Blueprint, request, render_template
from src.services.recommendation_service import (
    get_recommendations,
    get_explorador_recommendations,
    recomendar_artistas_para_usuario
)
from src.services.perfil_service import analizar_perfil_usuario

recommend_bp = Blueprint('recommend', __name__)

@recommend_bp.route("/", methods=["GET", "POST"])
def recommend():
    recomendaciones = []

    if request.method == "POST":
        user_id = request.form.get("user_id")
        genero = request.form.get("genero", "").strip() or None
        if user_id:
            recomendaciones = get_recommendations(user_id, genero)

    return render_template("index.html", recomendaciones=recomendaciones, modo="normal")

# Modo explorador
@recommend_bp.route("/explorador", methods=["GET", "POST"])
def modo_explorador():
    recomendaciones = []
    if request.method == "POST":
        user_id = request.form.get("user_id")
        level = request.form.get("level", 5, type=int)
        recomendaciones = get_explorador_recommendations(user_id, level=level)
        for reco in recomendaciones:
            reco["coincidencias"] = 1  # Para evitar errores en la UI
    return render_template("index.html", recomendaciones=recomendaciones, modo="explorador")

@recommend_bp.route("/perfil", methods=["GET", "POST"])
def perfil():
    perfil_info = {"mensaje": None, "generos_principales": [], "perfil": "desconocido"}

    # Aceptar ID por URL o por formulario
    user_id = request.values.get("user_id")

    if user_id:
        perfil_info = analizar_perfil_usuario(user_id)
    elif request.method == "POST":
        perfil_info["mensaje"] = "Debes ingresar un ID de usuario válido"

    return render_template("perfil.html", perfil_info=perfil_info)
