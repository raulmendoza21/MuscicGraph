from flask import Blueprint, redirect, request, session
from spotipy.oauth2 import SpotifyOAuth
from spotipy import Spotify
from pathlib import Path
import os
import shutil
from src.graph.graph_builder_full import construir_grafo_completo


from src.services.spotify_data_collector import MultiUserSpotifyDataCollector

auth_bp = Blueprint('auth_bp', __name__)

SPOTIPY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')

print("🔁 URI de redirección en uso:", SPOTIPY_REDIRECT_URI)

CACHE_DIR = Path(".spotify_caches")
CACHE_DIR.mkdir(exist_ok=True)

def get_spotify_oauth(cache_path=None):
    return SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope="user-read-private user-read-email user-top-read user-read-recently-played",
        show_dialog=True,
        cache_path=cache_path or ".spotify_caches/.cache-temp"
    )

@auth_bp.route('/auth')
def auth():
    oauth = get_spotify_oauth()
    auth_url = oauth.get_authorize_url()

    if "prompt=consent" not in auth_url:
        auth_url += "&prompt=consent" if "?" in auth_url else "?prompt=consent"

    return redirect(auth_url)

@auth_bp.route('/callback')
def callback():
    try:
        oauth = get_spotify_oauth()
        code = request.args.get('code')
        token_info = oauth.get_access_token(code)
        access_token = token_info['access_token']

        sp = Spotify(auth=access_token)
        user_profile = sp.current_user()
        user_id = user_profile['id']

        # ✅ Mueve el token temporal a uno único por usuario
        user_cache = CACHE_DIR / f".cache-{user_id}"
        shutil.move(".spotify_caches/.cache-temp", user_cache)

        # Re-autenticar con su cache propia
        oauth = get_spotify_oauth(cache_path=str(user_cache))
        token_info = oauth.get_cached_token()
        sp = Spotify(auth=token_info['access_token'])

        # Recolectar y guardar datos
        collector = MultiUserSpotifyDataCollector()
        user_data, tracks, playlists = collector.collect_user_data(sp)
        collector.store_user_data(user_data, tracks, playlists)

        construir_grafo_completo()
        session["user_id"] = user_id
        return redirect(f"/perfil?user_id={user_id}")

    except Exception as e:
        print(f"❌ Error en callback: {e}")
        return redirect("/")
