import json
import sys
import time
import os
import base64
from urllib.parse import urlencode
from http.server import HTTPServer, BaseHTTPRequestHandler

import dotenv
import requests
from requests import Response, get, post

from utils import Utils
from youtube_api import YoutubeAPI


class CustomHTTPServer(HTTPServer):
    """
    Custom HTTPServer class to store the authorization code

    Args:
        HTTPServer (_type_): _description_

    Attributes:
        auth_code : str
            The authorization code returned by the Spotify authorization server
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_code: str | None = None


class SpotifyAuthHandler(BaseHTTPRequestHandler):
    """
    Handle the authorization response from Spotify.

    Args:
    -----
        BaseHTTPRequestHandler (_type_): _description_

    Methods:
    --------
        do_GET(): 
            Handle GET requests
    """

    # This method name does not follow PEP 8 naming conventions
    # because it is required by the BaseHTTPRequestHandler class.
    def do_GET(self) -> None:
        """
        Handle GET requests from the Spotify authorization server.

        Returns:
            None
        """
        authorization_success_page = """
        <!DOCTYPE html>
        <html lang="en">
            <head>
                <meta charset="UTF-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                <meta name="description" content="Authorization Success" />
                <title>Authorization Success</title>
                <style>
                    html,
                    body {
                        height: 100%;
                        margin: 0;
                        background-color: black;
                        font-family: Arial, sans-serif;
                        color: white;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                    }
                    .container {
                        text-align: center;
                    }
                    h1 {
                        font-size: 2em;
                        color: white;
                    }
                    p {
                        color: #808080;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Authorization Successful</h1>
                    <p>You can now close this window and return to the terminal.</p>
                </div>
            </body>
        </html>
        """

        if self.path.startswith("/callback"):
            query = self.path.split('?', 1)[1]
            params = dict(qc.split('=') for qc in query.split('&'))
            code = params.get('code')
            self.send_response(200)
            self.end_headers()
            self.wfile.write(authorization_success_page.encode('utf-8'))
            self.server.auth_code = code


class SpotifyAPI:
    """
    Class to interact with the Spotify API.

    Attributes:
    -----------
    client_id : str | None
        The Spotify API client ID
    client_secret : str | None
        The Spotify API client secret
    user_id : str | None
        The Spotify user ID
    redirect_uri : str
        The redirect URI for the Spotify authorization server
    downloads_dir : str | None
        The directory where downloaded tracks will be saved
    auth_code : str | None
        The authorization code returned by the Spotify authorization server

    Methods:
    --------
    get_user_auth():
        Get the authorization code from the Spotify authorization server.
    get_token():
        Get the access token from the Spotify API.
    get_auth_header(token):
        Build the authorization header for Spotify API requests.
    get_playlist_response(token):
        Fetch the user's playlists from the Spotify API.
    extract_playlist_ids(playlists):
        Extract the playlist name and ID from the playlist response.
    get_playlists(token):
        Fetch the user's playlists & extract the playlist name and ID.
    get_track_response(playlist_id, token):
        Fetch the tracks from a playlist in the Spotify API.
    extract_track_details(track_response):
        Extract the track metadata from the track response.
    download_track_image(image_url):
        Download the album art for a track.
    get_tracks(playlist_id, token, existing_tracks, playlist_name):
        Download the tracks from a playlist.
    should_skip_track(metadata, existing_tracks):
        Check if a track should be skipped.
    handle_skip(download_complete, metadata):
        Handle skipping a track.
    handle_image_response(image_response, metadata):
        Handle the response from downloading the album art.
    handle_video_url(video_url, metadata, tracks_not_found):
        Handle the video URL from the YouTube API.
    download_track(
        youtube_api,
        video_title,
        video_url,
        playlist_name,
        metadata,
        number_of_downloads,
        total_download_time,
        number_of_tracks
    ):
        Download a track from YouTube.
    log_skip(metadata):
        Log that a track is being skipped.
    log_image_download_error(metadata):
        Log an error downloading the album art.
    log_download_progress(number_of_downloads, number_of_tracks, total_download_time):
        Log the download progress.
    """

    def __init__(self: object):
        dotenv.load_dotenv()
        self.client_id: str | None = os.getenv("CLIENT_ID")
        self.client_secret: str | None = os.getenv("CLIENT_SECRET")
        self.user_id: str | None = os.getenv("USER_ID")
        # Redirect URI is defined in the Spotify Developer Dashboard
        self.redirect_uri: str = "http://localhost:8080/callback"
        self.downloads_dir: str | None = os.getenv("DOWNLOADS_DIR")
        self.auth_code: str | None = None

        if not self.client_id or not self.client_secret or not self.user_id:
            print(
                "Please set the environment variables CLIENT_ID, CLIENT_SECRET and USER_ID.")
            sys.exit(1)

        if (
            self.client_id == "<Spotify API Client ID>" or
            self.client_secret == "<Spotify API Client Secret>" or
            self.user_id == "<Spotify User ID>"
        ):
            print(
                "Please set the environment variables CLIENT_ID, CLIENT_SECRET and USER_ID to their respective values.")
            sys.exit(1)

        if not self.downloads_dir:
            print(
                "Please set the environment variable DOWNLOADS_DIR to the directory "
                "where you want to save the downloaded tracks."
            )
            sys.exit(1)

    def get_user_auth(self: object) -> None:
        """
        Get the authorization code from the Spotify authorization server.

            Returns:
                    None
        """
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
        httpd = CustomHTTPServer(server_address, SpotifyAuthHandler)
        httpd.handle_request()

        self.auth_code = httpd.auth_code

    def get_token(self: object) -> str:
        """
        Get the access token from the Spotify API.

            Returns:
                    token (str): The access token for the Spotify API
        """
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

        try:
            result: Response = post(
                url, headers=headers, data=data, timeout=10)
        except requests.exceptions.Timeout:
            print("The request to fetch the access token timed out after 10 seconds.")
            sys.exit(1)
        except Exception as e:
            print(f"An error occurred while fetching the access token: {e}")
            sys.exit(1)

        result_json = json.loads(result.content)

        if "access_token" not in result_json:
            print("An error occurred while fetching the access token")
            sys.exit(1)

        token: str = result_json["access_token"]

        return token

    @staticmethod
    def get_auth_header(token: str) -> dict[str, str]:
        """
        Build the authorization header for Spotify API requests.

            Parameters:
                    token (str): The access token for the Spotify API

            Returns:
                    headers (dict[str, str]): The authorization header for Spotify API requests
        """
        headers: dict[str, str] = {
            "Authorization": "Bearer " + token
        }

        return headers

    def get_playlist_response(self: object, token: str) -> list[dict[str, str]]:
        """
        Fetch the user's playlists from the Spotify API.

                Parameters:
                        token (str): The access token for the Spotify API

                Returns:
                        playlists (list[dict[str, str]]): The user's playlists
        """
        url: str = f"https://api.spotify.com/v1/users/{self.user_id}/playlists"
        headers = self.get_auth_header(token)
        playlists: list[dict[str, str]] = []

        while url:
            # TODO: Add timeout & try-except block for request timeout errors
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

    @staticmethod
    def extract_playlist_ids(playlists: list[dict[str, str]]) -> list[tuple[str, str]]:
        """
        Extract the playlist name and ID from the playlist response.

            Parameters:
                    playlists (list[dict[str, str]]): The playlist response from the Spotify API

            Returns:
                    playlists_name_id (list[tuple[str, str]]): The playlist name and ID
        """
        playlists_name_id = []

        for playlist in playlists:
            name_id = (playlist["name"], playlist["id"])
            playlists_name_id.append(name_id)

        return playlists_name_id

    def get_playlists(self: object, token: str) -> list[tuple[str, str]]:
        """
        Fethces the user's playlists and extracts the playlist name and ID.

            Parameters:
                    token (str): The access token for the Spotify API

            Returns:
                    playlists (list[tuple[str, str]]): The playlist name and ID
        """
        playlists_response = self.get_playlist_response(token)
        playlists = self.extract_playlist_ids(playlists_response)

        return playlists

    def get_track_response(self: object, playlist_id: str, token: str) -> list[dict[str, str]]:
        tracks: list[dict[str, str]] = []
        url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        headers = self.get_auth_header(token)
        while url:
            # TODO: Add timeout & try-except block for request timeout errors
            response: Response = get(url, headers=headers)
            response_json = response.json()
            tracks.extend(response_json["items"])
            url: str = response_json["next"]

        return tracks

    @staticmethod
    def extract_track_details(track_response):
        track_details = []

        for track in track_response:
            metadata = {"search_string": "", "title": track["track"]["name"],
                        "artist": track["track"]["artists"][0]["name"], "album": "", "cover_art_url": "",
                        "cover_art": None}

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

    @staticmethod
    def download_track_image(image_url: str) -> Response | None:
        image_response = None

        try:
            image_response = get(image_url, timeout=10)
            image_response.raise_for_status()
        except requests.exceptions.Timeout:
            # Do nothing
            pass
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
                youtube_api,
                video_title,
                video_url,
                playlist_name,
                metadata,
                number_of_downloads,
                total_download_time,
                number_of_tracks
            )

            download_complete = True

        return tracks_not_found, number_of_downloads, number_of_skips

    @staticmethod
    def should_skip_track(metadata, existing_tracks):
        return metadata["title"] in existing_tracks

    @staticmethod
    def handle_skip(download_complete, metadata):
        if download_complete:
            print()
            download_complete = False

        skip_string = f"Skipping \"{metadata['search_string']}\" as it already exists."
        Utils.console_print(skip_string)
        return download_complete

    @staticmethod
    def handle_image_response(image_response, metadata):
        if image_response is None:
            image_download_error_string = (
                f"An error occurred while downloading the album art for \"{metadata['search_string']}\"."
            )
            Utils.console_print(image_download_error_string)
            return False
        metadata["cover_art"] = image_response.content
        return True

    @staticmethod
    def handle_video_url(video_url, metadata, tracks_not_found):
        if video_url is None:
            tracks_not_found.append(metadata["search_string"])
            return False
        return True

    def download_track(
        self,
        youtube_api,
        video_title,
        video_url,
        playlist_name,
        metadata,
        number_of_downloads,
        total_download_time,
        number_of_tracks
    ):
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

    @staticmethod
    def log_skip(metadata):
        skip_string = f"Skipping \"{metadata['search_string']}\" as it already exists."
        Utils.console_print(skip_string)

    @staticmethod
    def log_image_download_error(metadata):
        image_download_error_string = (
            f"An error occurred while downloading the album art for \"{metadata['search_string']}\"."
        )
        Utils.console_print(image_download_error_string)

    @staticmethod
    def log_download_progress(number_of_downloads, number_of_tracks, total_download_time):
        average_download_time = total_download_time / number_of_downloads
        estimated_time_remaining = average_download_time * \
            (number_of_tracks - number_of_downloads)
        minutes, seconds = divmod(estimated_time_remaining, 60)

        sys.stdout.write(
            f"Downloaded [{number_of_downloads}/{number_of_tracks}] tracks "
            f"({number_of_downloads / number_of_tracks * 100:.2f}%) - "
            f"Estimated total time remaining: {int(minutes)}m {int(seconds)}s\r"
        )
        sys.stdout.flush()
