import dotenv
import os
import base64
import json
import sys
import time
from requests import get, post
from urllib.parse import urlencode
from http.server import HTTPServer, BaseHTTPRequestHandler

from utils import Utils
from youtube_api import YoutubeAPI


class SpotifyAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/callback"):
            query = self.path.split('?', 1)[1]
            params = dict(qc.split('=') for qc in query.split('&'))
            code = params.get('code')
            self.send_response(200)
            self.end_headers()
            with open('authorization_success.html', 'r') as file:
                html_content = file.read()
            self.wfile.write(html_content.encode('utf-8'))
            self.server.auth_code = code


class SpotifyAPI:
    def __init__(self):
        dotenv.load_dotenv()
        self.client_id = os.getenv("CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET")
        self.user_id = os.getenv("USER_ID")
        self.redirect_uri = os.getenv("REDIRECT_URI")
        self.downloads_dir = os.getenv("DOWNLOADS_DIR")
        self.auth_code = None

    def get_user_auth(self):
        auth_url = "https://accounts.spotify.com/authorize"
        state = Utils.random_string(16)
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "scope": "playlist-read-private",
            "redirect_uri": self.redirect_uri,
            "state": state,
        }
        url = f"{auth_url}?{urlencode(params)}"
        print(
            f"Please open the following URL in your browser to authorize the application:\n{url}")

        # Start a local server to handle the redirect
        server_address = ('', 8080)
        httpd = HTTPServer(server_address, SpotifyAuthHandler)
        httpd.handle_request()

        self.auth_code = httpd.auth_code

    def get_token(self):
        auth_string = self.client_id + ":" + self.client_secret
        auth_bytes = auth_string.encode("utf-8")
        auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

        url = "https://accounts.spotify.com/api/token"
        headers = {
            "Authorization": "Basic " + auth_base64,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "authorization_code",
            "code": self.auth_code,
            "redirect_uri": self.redirect_uri,
        }
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
        playlists = []

        while url:
            response = get(url, headers=headers)
            response_json = response.json()

            # if response code not 200, print error message
            if response.status_code != 200:
                print(
                    f"An error occurred while fetching playlists: {response_json['error']['message']}")
                break

            playlists.extend(response_json["items"])
            url = response_json["next"]

        return playlists

    def extract_playlist_ids(self, playlists):
        playlists_name_id = []

        for playlist in playlists:
            name_id = (playlist["name"], playlist["id"])
            playlists_name_id.append(name_id)

        return playlists_name_id

    def get_playlists(self, token):
        playlists_response = self.get_playlist_response(token)
        playlists = self.extract_playlist_ids(playlists_response)

        return playlists

    def get_track_response(self, playlist_id, token):
        tracks = []
        url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        headers = self.get_auth_header(token)
        while url:
            response = get(url, headers=headers)
            response_json = response.json()
            tracks.extend(response_json["items"])
            url = response_json["next"]

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

            metadata["search_string"] = metadata["title"] + \
                " - " + metadata["artist"]
            metadata["title"] = Utils.sanitize_filename(
                metadata["search_string"])

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
        number_of_tracks = len(track_details) - len(existing_tracks)

        download_complete = False
        total_download_time = 0

        for metadata in track_details:
            if self.should_skip_track(metadata, existing_tracks):
                number_of_skips += 1
                download_complete = self.handle_skip(
                    download_complete, metadata)
                continue

            image_response = self.download_track_image(
                metadata["cover_art_url"])
            if not self.handle_image_response(image_response, metadata):
                continue

            youtube_api = YoutubeAPI()
            video_url, video_title = youtube_api.get_video_url(
                metadata["search_string"])
            if not self.handle_video_url(video_url, metadata, tracks_not_found):
                continue

            number_of_downloads, total_download_time = self.download_track(
                youtube_api, video_title, video_url, playlist_name, metadata, number_of_downloads, total_download_time, number_of_tracks)

            download_complete = True

        return tracks_not_found, number_of_downloads, number_of_skips

    def should_skip_track(self, metadata, existing_tracks):
        return metadata["title"] in existing_tracks

    def handle_skip(self, download_complete, metadata):
        if download_complete:
            print()
            download_complete = False

        skip_string = f"Skipping \"{metadata['search_string']}\" as it already exists."
        Utils.console_print(skip_string)
        return download_complete

    def handle_image_response(self, image_response, metadata):
        if image_response is None:
            image_download_error_string = f"An error occurred while downloading the album art for \"{metadata['search_string']}\"."
            Utils.console_print(image_download_error_string)
            return False
        metadata["cover_art"] = image_response.content
        return True

    def handle_video_url(self, video_url, metadata, tracks_not_found):
        if video_url is None:
            tracks_not_found.append(metadata["search_string"])
            return False
        return True

    def download_track(self, youtube_api, video_title, video_url, playlist_name, metadata, number_of_downloads, total_download_time, number_of_tracks):
        if video_title is None:
            video_title = ""

        start_time = time.time()
        youtube_api.download_song_wrapper(
            video_title, video_url, playlist_name, metadata)
        end_time = time.time()

        download_time = end_time - start_time
        total_download_time += download_time

        number_of_downloads += 1
        self.log_download_progress(
            number_of_downloads, number_of_tracks, total_download_time)

        return number_of_downloads, total_download_time

    def log_skip(self, metadata):
        skip_string = f"Skipping \"{metadata['search_string']}\" as it already exists."
        Utils.console_print(skip_string)

    def log_image_download_error(self, metadata):
        image_download_error_string = f"An error occurred while downloading the album art for \"{metadata['search_string']}\"."
        Utils.console_print(image_download_error_string)

    def log_download_progress(self, number_of_downloads, number_of_tracks, total_download_time):
        average_download_time = total_download_time / number_of_downloads
        estimated_time_remaining = average_download_time * \
            (number_of_tracks - number_of_downloads)
        minutes, seconds = divmod(estimated_time_remaining, 60)

        sys.stdout.write(
            f"Downloaded [{number_of_downloads}/{number_of_tracks}] tracks ({number_of_downloads/number_of_tracks*100:.2f}%) - Estimated total time remaining: {int(minutes)}m {int(seconds)}s\r")
        sys.stdout.flush()
