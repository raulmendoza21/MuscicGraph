import os
import time
import datetime
import spotipy
from spotipy.exceptions import SpotifyException
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

class MultiUserSpotifyDataCollector:
    def __init__(self):
        self.scope = 'user-library-read user-top-read playlist-read-private'
        client = MongoClient(os.getenv("MONGODB_URI"))
        self.db = client[os.getenv("MONGODB_DATABASE")]

    def _get_artist_genres_bulk(self, sp, artist_ids):
        genres_map = {}
        try:
            for i in range(0, len(artist_ids), 50):
                chunk = artist_ids[i:i+50]
                success = False
                retries = 3
                while not success and retries > 0:
                    try:
                        artists_data = sp.artists(chunk)['artists']
                        for artist in artists_data:
                            genres_map[artist['id']] = artist.get('genres', [])
                        success = True
                        time.sleep(0.3)
                    except SpotifyException as e:
                        if e.http_status == 429:
                            wait_time = int(e.headers.get('Retry-After', 2))
                            print(f"⚠️ Rate limit alcanzado. Esperando {wait_time} segundos...")
                            time.sleep(wait_time)
                        else:
                            print(f"❌ Error al obtener géneros: {e}")
                            retries -= 1
        except Exception as e:
            print(f"❌ Error general en recolección de géneros: {e}")
        return genres_map

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
        artist_ids = list({a['id'] for t in top_tracks['items'] for a in t['artists']})
        genres_map = self._get_artist_genres_bulk(sp, artist_ids)

        processed_tracks = []
        for track in top_tracks['items']:
            processed_tracks.append({
                'spotify_id': track['id'],
                'name': track['name'],
                'artists': [
                    {
                        'spotify_id': a['id'],
                        'name': a['name'],
                        'genres': genres_map.get(a['id'], [])
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
            time.sleep(0.05)

        # 📂 PLAYLISTS
        playlists = sp.current_user_playlists(limit=5)
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
                playlist_tracks = sp.playlist_tracks(playlist['id'], limit=30)
                artist_ids = list({a['id'] for item in playlist_tracks['items']
                                  if item.get('track') for a in item['track']['artists']})
                genres_map = self._get_artist_genres_bulk(sp, artist_ids)

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
                                'genres': genres_map.get(a['id'], [])
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
                    time.sleep(0.05)
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
