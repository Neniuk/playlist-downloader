from dotenv import load_dotenv
import os
import base64
from requests import post, get
import json
import string, secrets
from youtubesearchpython import VideosSearch
from pytube import YouTube

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
user_id = os.getenv("USER_ID")

def random_string(size):        
    letters = string.ascii_lowercase+string.ascii_uppercase+string.digits            
    return ''.join(secrets.choice(letters) for i in range(size))


def get_token():
    auth_string = client_id + ":" + client_secret
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


def get_auth_header(token):
    headers = {
        "Authorization": "Bearer " + token
    }
    return headers


def get_playlists(user_id, token):
    playlist_id = []
    url = f"https://api.spotify.com/v1/users/{user_id}/playlists"
    headers = get_auth_header(token)
    response = get(url, headers=headers)
    response_json = response.json()
    playlists = response_json["items"]
    
    playlist_id = []
    
    for playlist in playlists:
        # print(playlist["name"], playlist["id"])
        name_id = (playlist["name"], playlist["id"])
        playlist_id.append(name_id)
    
    return playlist_id


def get_tracks(playlist_id, token):
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = get_auth_header(token)
    response = get(url, headers=headers)
    response_json = response.json()
    tracks = response_json["items"]
    
    track_list = []
    
    for track in tracks:
        track_name = track["track"]["name"]
        artist = track["track"]["artists"][0]["name"]
        search_string = track_name + " - " + artist
        video_url = get_video_url(search_string)
        
        if video_url is not None:
            track_list.append(video_url)
        # print(track_list)
    return track_list

def get_video_url(song_name):
    videosSearch = VideosSearch(song_name, limit = 1)
    result = videosSearch.result()
    
    if result["result"] == []: 
        return None
    
    video_url = result["result"][0]["link"]
    
    return video_url


def download_video(video_url):
    yt = YouTube(video_url, use_oauth=True, allow_oauth_cache=True)
    video = yt.streams.filter(only_audio=True).first()
    print("Downlaoding: ", yt.title)
    video.download()
    print("Download complete.")


def main():
    token = get_token()
    playlists = get_playlists(user_id, token)
    
    print("Playlists:\n")
    i = 0
    for playlist in playlists:
        print(f"{i}. {playlist[0]}")
        i += 1
    
    # playlist_index = input("\nPlease enter the index of the playlist you wish to download: ")
    
    # if playlist_index.isdigit() and (int_index >= 0) and (int_index < playlists.len()):
    #     int_index = int(playlist_index)
    #     songs = get_songs(playlists[int_index][1])
    # else:
    #     print("Invalid index.")
    playlist_id = str(playlists[0][1])
    tracks = get_tracks(playlist_id, token)
    
    download_video(tracks[0])

main()

