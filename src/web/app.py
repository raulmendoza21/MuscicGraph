import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from flask import Flask, render_template, request
from src.recommenders.recommender import recomendar_artistas_para_usuario

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    recomendaciones = []
    if request.method == "POST":
        user_id = request.form.get("user_id")
        genero = request.form.get("genero")

        recomendaciones = recomendar_artistas_para_usuario(user_id, genero=genero if genero else None)

    return render_template("index.html", recomendaciones=recomendaciones)

if __name__ == "__main__":
    app.run(debug=True)
