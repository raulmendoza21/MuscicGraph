from flask import Blueprint, redirect, request, session
from spotipy.oauth2 import SpotifyOAuth
import os
from src.services.spotify_data_collector import MultiUserSpotifyDataCollector
import spotipy
auth_bp = Blueprint('auth_bp', __name__)

# Configuración Spotify
SPOTIPY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID', 'tu_client_id')
SPOTIPY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET', 'tu_client_secret')
SPOTIPY_REDIRECT_URI = os.environ.get('SPOTIFY_REDIRECT_URI', 'http://localhost:5000/callback')
SCOPE = 'user-read-private user-read-email user-top-read user-read-recently-played'

def get_spotify_oauth():
    return SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope=SCOPE
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

    token_info = get_spotify_oauth().get_access_token(code)
    session['token_info'] = token_info
    access_token = token_info['access_token']
    
    # Recolección de datos Spotify
    try:
        sp = spotipy.Spotify(auth=access_token)
        collector = MultiUserSpotifyDataCollector()
        user_data, tracks, playlists = collector.collect_user_data(sp)
        collector.store_user_data(user_data, tracks, playlists)
        session["user_id"] = user_data["spotify_id"]
    except Exception as e:
        print(f"❌ Error al recolectar datos: {e}")
        return redirect("/")

    return redirect(f"/perfil?user_id={user_data['spotify_id']}")

