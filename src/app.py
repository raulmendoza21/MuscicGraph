from flask import Flask
from src.api import register_blueprints
from dotenv import load_dotenv
from pathlib import Path
import os

def create_app():

    load_dotenv()   

    # Crear instancia de Flask
    app = Flask(__name__, template_folder="web/templates")

    # Registrar rutas (blueprints)
    register_blueprints(app)

    # Clave de sesión segura (para auth con Spotify)
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecret")

    return app

# Ejecutar si se lanza directamente
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=8888)
