from dotenv import load_dotenv
import os
import base64
from requests import post, get
import json
import string, secrets
from youtubesearchpython import VideosSearch
from pytube import YouTube
import re
import subprocess

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
user_id = os.getenv("USER_ID")
downloads_dir = os.getenv("DOWNLOADS_DIR")

def get_existing_tracks():
    existing_tracks = []
    for filename in os.listdir("./" + downloads_dir):
        if filename.endswith(".mp4"):
            existing_tracks.append(filename[:-4])
    return existing_tracks

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


def get_tracks(playlist_id, token, existing_tracks):
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = get_auth_header(token)
    response = get(url, headers=headers)
    response_json = response.json()
    tracks = response_json["items"]
    
    tracks_not_found = []
    
    for track in tracks:
        track_name = track["track"]["name"]
        artist = track["track"]["artists"][0]["name"]
        
        search_string = track_name + " - " + artist
        sanitized_track_name = sanitize_filename(search_string)
        
        if sanitized_track_name in existing_tracks:
            print(f"Skipping {search_string} as it already exists.")
            continue
        
        video_url = get_video_url(search_string)
        
        if video_url is None:
            tracks_not_found.append(search_string)
            continue
        
        if video_url is not None:
            download_song(video_url, sanitized_track_name)
            
    return tracks_not_found

def get_video_url(song_name):
    videosSearch = VideosSearch(song_name, limit = 1)
    result = videosSearch.result()
    
    if result["result"] == []: 
        return None
    
    video_url = result["result"][0]["link"]
    
    return video_url


def download_song(video_url, song_title):
    yt = YouTube(video_url, use_oauth=True, allow_oauth_cache=True)
    audio = yt.streams.filter(only_audio=True).first()
    print("Downlaoding: ", yt.title)
    
    song_title = sanitize_filename(song_title)
    output_file = audio.download(output_path=os.path.join(downloads_dir), filename=song_title + ".mp4")
    print("OUTPUT FILE:" + output_file)
    mp3_file = os.path.splitext(output_file)[0] + '.mp3'
    print("MP3 FILE:" + mp3_file)
    subprocess.run(['ffmpeg', '-i', output_file, '-vn', '-ab', '128k', '-ar', '44100', '-y', mp3_file], shell=True)
    
    if os.path.exists(output_file):
        os.remove(output_file)
    
    print("Download complete.\n")


def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "", filename)


def main():
    token = get_token()
    
    existing_tracks = get_existing_tracks()
    
    playlists = get_playlists(user_id, token)
    
    print("Playlists:\n")
    i = 0
    for playlist in playlists:
        print(f"{i}. {playlist[0]}")
        i += 1
        
    print("")
    
    # playlist_index = input("\nPlease enter the index of the playlist you wish to download: ")
    
    # if playlist_index.isdigit() and (int_index >= 0) and (int_index < playlists.len()):
    #     int_index = int(playlist_index)
    #     songs = get_songs(playlists[int_index][1])
    # else:
    #     print("Invalid index.")
    
    playlist_id = str(playlists[0][1])
    print(playlists[0][1])
    print("")
    
    tracks_not_found = get_tracks(playlist_id, token, existing_tracks)
    
    print("All downloads complete.\n")
    
    if len(tracks_not_found) == 0:
        print("All tracks found.")
    else:
        print("Tracks not found:\n")
        for track in tracks_not_found:
            print(track)

main()

