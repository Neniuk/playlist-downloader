import dotenv
import os
import base64
import json
from requests import get, post

from utils import Utils
from youtube_api import YoutubeAPI

class SpotifyAPI:
    def __init__(self):
        dotenv.load_dotenv()
        self.client_id = os.getenv("CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET")
        self.user_id = os.getenv("USER_ID")
        self.downloads_dir = os.getenv("DOWNLOADS_DIR")


    def get_token(self):
        auth_string = self.client_id + ":" + self.client_secret
        auth_bytes = auth_string.encode("utf-8")
        auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")
        
        url = "https://accounts.spotify.com/api/token"
        headers = {
            "Authorization": "Basic " + auth_base64,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"grant_type": "client_credentials"}
        result = post(url, headers=headers, data=data)
        result_json = json.loads(result.content)
        token = result_json["access_token"]
        
        return token


    def get_auth_header(self, token):
        headers = {
            "Authorization": "Bearer " + token
        }
        
        return headers


    def get_playlist_response(self, token):
        url = f"https://api.spotify.com/v1/users/{self.user_id}/playlists"
        headers = self.get_auth_header(token)
        response = get(url, headers=headers)
        response_json = response.json()
        playlists = response_json["items"]
        
        return playlists


    def extract_playlist_ids(self, playlists):
        playlists_name_id = []
    
        for playlist in playlists:
            # print(playlist["name"], playlist["id"])
            name_id = (playlist["name"], playlist["id"])
            playlists_name_id.append(name_id)
        
        return playlists_name_id


    def get_playlists(self, token):
        playlists_response = self.get_playlist_response(token)
        playlists = self.extract_playlist_ids(playlists_response)
        
        return playlists


    def get_track_response(self, playlist_id, token):
        url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        headers = self.get_auth_header(token)
        response = get(url, headers=headers)
        response_json = response.json()
        tracks = response_json["items"]
        
        return tracks


    def extract_track_details(self, track_response):
        track_details = []
        
        for track in track_response:
            metadata = {
                "search_string": "",
                "title": "",
                "artist": "",
                "album": "",
                "cover_art_url": "",
                "cover_art": None
            }
            
            metadata["title"] = track["track"]["name"]
            metadata["artist"] = track["track"]["artists"][0]["name"]
            
            metadata["search_string"] = metadata["title"] + " - " + metadata["artist"]
            metadata["title"] = Utils.sanitize_filename(metadata["search_string"])
            
            album = track["track"]["album"]
            
            album_name = album["name"]
            images = album["images"]
            
            metadata["album"] = album_name
            
            if images:
                metadata["cover_art_url"] = images[0]["url"]
                track_details.append(metadata)
        
        return track_details


    def download_track_image(self, image_url):
        image_response = None
        
        try:
            image_response = get(image_url)
            image_response.raise_for_status()
        except Exception as e:
            print(f"An error occurred while downloading the album art: {e}")
        
        return image_response


    def get_tracks(self, playlist_id, token, existing_tracks, playlist_name):
        track_response = self.get_track_response(playlist_id, token)
        track_details = self.extract_track_details(track_response)
        
        tracks_not_found = []
        number_of_downloads = 0
        number_of_skips = 0
        
        download_complete = False
        for metadata in track_details:
            if metadata["title"] in existing_tracks:
                number_of_skips += 1
                
                if download_complete:
                    print()
                    download_complete = False
                
                skip_string = f"Skipping \"{metadata['search_string']}\" as it already exists."
                Utils.console_print(skip_string)
                continue

            image_response = self.download_track_image(metadata["cover_art_url"])
            metadata["cover_art"] = image_response.content
            
            if image_response is None:
                image_download_error_string = f"An error occurred while downloading the album art for \"{metadata['search_string']}\"."
                Utils.console_print(image_download_error_string)
                continue
            
            youtube_api = YoutubeAPI()

            video_url = youtube_api.get_video_url(metadata["search_string"])
            if video_url is None:
                tracks_not_found.append(metadata["search_string"])
                continue
            
            if video_url is not None:
                youtube_api.download_song(video_url, playlist_name, metadata)
                download_complete = True
                number_of_downloads += 1

        return tracks_not_found, number_of_downloads, number_of_skips

