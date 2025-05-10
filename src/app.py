from flask import Flask
from src.api import register_blueprints
from dotenv import load_dotenv
from pathlib import Path
import os

def create_app():
    # Cargar variables de entorno
        # ✅ Cargar .env desde la raíz ANTES de cualquier otro import
    load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")   

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
    app.run(debug=True)
