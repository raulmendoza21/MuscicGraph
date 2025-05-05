import os
import time
import datetime
import spotipy
from spotipy.util import prompt_for_user_token
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

class MultiUserSpotifyDataCollector:
    def __init__(self):
        self.scope = 'user-library-read user-top-read playlist-read-private'
        client = MongoClient(os.getenv("MONGODB_URI"))
        self.db = client[os.getenv("MONGODB_DATABASE")]

    def authenticate_user(self, username):
        token = prompt_for_user_token(
            username=username,
            scope=self.scope,
            client_id=os.getenv('SPOTIFY_CLIENT_ID'),
            client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
            redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI')
        )
        if not token:
            raise Exception("❌ No se pudo obtener el token de autenticación.")
        
        sp = spotipy.Spotify(auth=token)
        return sp, token

    def collect_user_data(self, sp):
        user_profile = sp.current_user()
        now = datetime.datetime.utcnow()

        user_data = {
            'spotify_id': user_profile['id'],
            'display_name': user_profile['display_name'],
            'followers': user_profile['followers']['total'],
            'country': user_profile.get('country'),
            'images': user_profile.get('images', []),
            'collected_at': now
        }

        # 🎵 TOP TRACKS
        top_tracks = sp.current_user_top_tracks(limit=50, time_range='medium_term')
        processed_tracks = []
        for track in top_tracks['items']:
            processed_tracks.append({
                'spotify_id': track['id'],
                'name': track['name'],
                'artists': [
                    {
                        'spotify_id': a['id'],
                        'name': a['name'],
                        'genres': sp.artist(a['id']).get('genres', [])
                    } for a in track['artists']
                ],
                'album': {
                    'spotify_id': track['album']['id'],
                    'name': track['album']['name'],
                    'release_date': track['album'].get('release_date')
                },
                'popularity': track['popularity'],
                'user_spotify_id': user_profile['id'],
                'source': 'top_tracks',
                'collected_at': now
            })
            time.sleep(0.1)  # Para evitar rate limiting de Spotify

        # 📂 PLAYLISTS
        playlists = sp.current_user_playlists(limit=20)
        processed_playlists = []
        playlist_track_entries = []

        for playlist in playlists['items']:
            processed_playlists.append({
                'spotify_id': playlist['id'],
                'name': playlist['name'],
                'owner': {
                    'spotify_id': playlist['owner']['id'],
                    'display_name': playlist['owner']['display_name']
                },
                'tracks_count': playlist['tracks']['total'],
                'public': playlist['public'],
                'user_spotify_id': user_profile['id'],
                'collected_at': now
            })

            try:
                playlist_tracks = sp.playlist_tracks(playlist['id'], limit=50)
                for item in playlist_tracks['items']:
                    track = item.get('track')
                    if not track or not track.get('id'):
                        continue
                    playlist_track_entries.append({
                        'spotify_id': track['id'],
                        'name': track['name'],
                        'artists': [
                            {
                                'spotify_id': a['id'],
                                'name': a['name'],
                                'genres': sp.artist(a['id']).get('genres', [])
                            } for a in track['artists']
                        ],
                        'album': {
                            'spotify_id': track['album']['id'],
                            'name': track['album']['name'],
                            'release_date': track['album'].get('release_date')
                        },
                        'popularity': track['popularity'],
                        'user_spotify_id': user_profile['id'],
                        'source': 'playlist',
                        'collected_at': now
                    })
                    time.sleep(0.1)
            except Exception as e:
                print(f"⚠️ No se pudieron procesar los tracks de la playlist {playlist['name']}: {e}")

        all_tracks = processed_tracks + playlist_track_entries
        return user_data, all_tracks, processed_playlists

    def store_user_data(self, user_data, tracks, playlists):
        self.db['users'].update_one(
            {'spotify_id': user_data['spotify_id']},
            {'$set': user_data},
            upsert=True
        )

        for track in tracks:
            self.db['top_tracks'].update_one(
                {'spotify_id': track['spotify_id'], 'user_spotify_id': track['user_spotify_id']},
                {'$set': track},
                upsert=True
            )

        for playlist in playlists:
            self.db['playlists'].update_one(
                {'spotify_id': playlist['spotify_id'], 'user_spotify_id': playlist['user_spotify_id']},
                {'$set': playlist},
                upsert=True
            )

        print(f"✅ Datos de usuario {user_data['display_name']} almacenados correctamente.")

    def add_multiple_users(self, num_users=1):
        for i in range(num_users):
            print(f"\n👤 Añadiendo usuario {i + 1}/{num_users}")
            try:
                username = input("🔑 Introduce el nombre de usuario de Spotify (único): ")
                sp, token_info = self.authenticate_user(username)
                user_data, tracks, playlists = self.collect_user_data(sp)
                self.store_user_data(user_data, tracks, playlists)
            except Exception as e:
                print(f"❌ Error añadiendo usuario: {e}")

