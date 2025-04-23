import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def get_spotify_client():
    """
    Crear cliente de Spotify con autenticación OAuth
    """
    return spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=os.getenv('SPOTIFY_CLIENT_ID'),
            client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
            redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI'),
            scope=(
                'user-library-read '
                'user-top-read '
                'playlist-read-private'
            )
        )
    )

def fetch_user_info(sp):
    """
    Obtener información básica del usuario
    """
    user_profile = sp.current_user()
    return {
        'id': user_profile['id'],
        'display_name': user_profile['display_name'],
        'followers': user_profile['followers']['total']
    }

def fetch_user_top_tracks(sp):
    """
    Obtener las mejores canciones del usuario
    """
    return sp.current_user_top_tracks(limit=10, time_range='medium_term')

def main():
    try:
        # Obtener cliente de Spotify
        sp = get_spotify_client()
        
        # Obtener información del usuario
        user_info = fetch_user_info(sp)
        print("Información de Usuario:")
        print(f"ID: {user_info['id']}")
        print(f"Nombre: {user_info['display_name']}")
        print(f"Seguidores: {user_info['followers']}")
        
        print("\nMejores Canciones:")
        # Obtener mejores canciones
        top_tracks = fetch_user_top_tracks(sp)
        for track in top_tracks['items']:
            print(f"Canción: {track['name']}")
            print(f"Artista: {track['artists'][0]['name']}")
            print("---")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()