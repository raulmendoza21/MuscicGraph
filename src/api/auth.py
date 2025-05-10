from flask import Blueprint, redirect, request, session
from spotipy.oauth2 import SpotifyOAuth
from spotipy import Spotify
from dotenv import load_dotenv
from pathlib import Path
import os

from src.services.spotify_data_collector import MultiUserSpotifyDataCollector

auth_bp = Blueprint('auth_bp', __name__)

# 🔁 Cargar .env desde la raíz
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")

SPOTIPY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID', 'tu_client_id')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET', 'tu_client_secret')
SPOTIPY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')

print("🔁 URI de redirección en uso:", SPOTIPY_REDIRECT_URI)

def get_spotify_oauth():
    return SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope="user-read-private user-read-email user-top-read user-read-recently-played"
    )

@auth_bp.route('/auth')
def auth():
    username = request.args.get('username')
    if not username:
        return redirect('/')
    session['username'] = username
    auth_url = get_spotify_oauth().get_authorize_url()
    return redirect(auth_url)

@auth_bp.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return redirect('/')

    try:
        oauth = get_spotify_oauth()
        token_info = oauth.get_access_token(code)
        session['token_info'] = token_info
        access_token = token_info['access_token']

        sp = Spotify(auth=access_token)
        collector = MultiUserSpotifyDataCollector()
        user_data, tracks, playlists = collector.collect_user_data(sp)
        collector.store_user_data(user_data, tracks, playlists)

        session["user_id"] = user_data["spotify_id"]
        return redirect(f"/perfil?user_id={user_data['spotify_id']}")

    except Exception as e:
        print(f"❌ Error al recolectar datos: {e}")
        return redirect("/")
