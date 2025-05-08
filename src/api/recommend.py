from flask import Blueprint, request, render_template, session, jsonify
from src.services.recommendation_service import (
    get_recommendations,
    get_explorador_recommendations,
    get_discovery_recommendations
)
from src.services.perfil_service import analizar_perfil_usuario

recommend_bp = Blueprint('recommend', __name__)

# Página principal + recomendaciones personalizadas por AJAX
@recommend_bp.route("/", methods=["GET", "POST"])
def recommend():
    if request.method == "POST":
        user_id = request.form.get("user_id") or session.get("user_id")
        genero = request.form.get("genero", "").strip() or None

        if user_id:
            recomendaciones = get_recommendations(user_id, genero)
            return jsonify(recomendaciones=recomendaciones)

        return jsonify(recomendaciones=[])

    return render_template("index.html")


# Modo explorador por AJAX
@recommend_bp.route("/explorador", methods=["POST"])
def modo_explorador():
    user_id = request.form.get("user_id") or session.get("user_id")
    level = request.form.get("level", 5, type=int)

    if user_id:
        recomendaciones = get_explorador_recommendations(user_id, level=level)
        for reco in recomendaciones:
            reco["coincidencias"] = reco.get("coincidencias", 1)
        return jsonify(recomendaciones=recomendaciones)

    return jsonify(recomendaciones=[])


# Modo descubrimiento por AJAX
@recommend_bp.route("/descubrimiento", methods=["POST"])
def modo_descubrimiento():
    user_id = request.form.get("user_id") or session.get("user_id")
    limite = request.form.get("limite", 10, type=int)

    if user_id:
        recomendaciones = get_discovery_recommendations(user_id, limite=limite)
        for reco in recomendaciones:
            reco["coincidencias"] = reco.get("coincidencias", 1)
        return jsonify(recomendaciones=recomendaciones)

    return jsonify(recomendaciones=[])


# Página de perfil (mantiene renderizado tradicional)
@recommend_bp.route("/perfil", methods=["GET", "POST"])
def perfil():
    perfil_info = {
        "mensaje": "Introduce tu ID de Spotify para ver tu perfil musical.",
        "generos_principales": [],
        "perfil": "desconocido"
    }

    # Limpiar sesión para evitar carga automática
    if request.method == "GET":
        session.pop("user_id", None)

    user_id = request.values.get("user_id")

    if user_id:
        perfil_info = analizar_perfil_usuario(user_id)
    elif request.method == "POST":
        perfil_info["mensaje"] = "Debes ingresar un ID de usuario válido"

    return render_template("perfil.html", perfil_info=perfil_info, user_id=user_id)

