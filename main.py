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
import time
import http.client
import locale
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, error

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
user_id = os.getenv("USER_ID")
downloads_dir = os.getenv("DOWNLOADS_DIR")
keep_mp4_without_ffmpeg = os.getenv("KEEP_MP4_WITHOUT_FFMPEG")

def get_existing_tracks(playlist_name):
    existing_tracks = []
    for filename in os.listdir("./" + downloads_dir + "/" + playlist_name):
        if filename.endswith(".mp3"):
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


def get_tracks(playlist_id, token, existing_tracks, playlist_name):
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = get_auth_header(token)
    response = get(url, headers=headers)
    response_json = response.json()
    tracks = response_json["items"]
    
    tracks_not_found = []
    number_of_downloads = 0
    number_of_skips = 0
    
    download_complete = False
    for track in tracks:
        track_name = track["track"]["name"]
        artist = track["track"]["artists"][0]["name"]
        
        album = track["track"]["album"]
        images = album["images"]
        if images:
            image_url = images[0]["url"]
            image_response = None
            
            try:
                image_response = get(image_url)
                image_response.raise_for_status()
            except Exception as e:
                print(f"An error occurred while downloading the album art: {e}")

        search_string = track_name + " - " + artist
        sanitized_track_name = sanitize_filename(search_string)
        
        if sanitized_track_name in existing_tracks:
            number_of_skips += 1
            
            if download_complete:
                print()
                download_complete = False
            
            skip_print_string = f"Skipping \"{search_string}\" as it already exists."
            console_print(skip_print_string)
            continue
        
        video_url = get_video_url(search_string)
        
        if video_url is None:
            tracks_not_found.append(search_string)
            continue
        
        if video_url is not None:
            download_song(video_url, sanitized_track_name, playlist_name, image_response.content)
            download_complete = True
            number_of_downloads += 1
            
    return tracks_not_found, number_of_downloads, number_of_skips

def get_video_url(song_name):
    videosSearch = VideosSearch(song_name, limit = 1)
    result = videosSearch.result()
    
    if result["result"] == []: 
        return None
    
    video_url = result["result"][0]["link"]
    
    return video_url


def download_song(video_url, song_title, playlist_name, cover_art):
    yt = YouTube(video_url, use_oauth=True, allow_oauth_cache=True)
    audio = yt.streams.filter(only_audio=True).first()
    
    download_print_string = f"\nDownloading: {yt.title}"
    console_print(download_print_string)
    
    song_title = sanitize_filename(song_title)
    output_file = None
    
    # Retry up to 3 times
    for _ in range(3):
        try:
            output_file = audio.download(output_path=os.path.join(downloads_dir, playlist_name), filename=song_title + ".mp4")
            # print("OUTPUT FILE:" + output_file)
            break
        except http.client.IncompleteRead:
            print("IncompleteRead error, retrying download...")
            time.sleep(1)
        except Exception as e:
            print(f"An error occurred during download: {e}")
            time.sleep(1)

    if output_file is None:
        print("Failed to download after 5 attempts.")
        return
    
    mp3_file = os.path.splitext(output_file)[0] + '.mp3'
    # print("MP3 FILE:" + mp3_file)
    
    print("Converting to mp3...")

    conversion_successful = False
    
    try:
        subprocess.run(['ffmpeg', '-i', output_file, '-vn', '-ab', '128k', '-ar', '44100', '-y', mp3_file], 
                       stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, shell=True)
        conversion_successful = True
    except KeyboardInterrupt:
        print("Conversion was interrupted by the user.")
        if os.path.exists(mp3_file):
            os.remove(mp3_file)
    except Exception as e:
        print(f"An error occurred during conversion: {e}")
        if os.path.exists(mp3_file):
            os.remove(mp3_file)
    finally:
        if conversion_successful and os.path.exists(mp3_file) and (cover_art is not None):
            print("Adding cover art...")
            
            audio = MP3(mp3_file, ID3=ID3)
            audio.tags.add(
                APIC(
                    encoding=3,
                    mime='image/jpeg',
                    type=3,
                    desc=u'Cover',
                    data=cover_art
                )
            )
            
            audio.save()
        
        if keep_mp4_without_ffmpeg == "0" and os.path.exists(output_file):
            os.remove(output_file)
        else:
            if conversion_successful and os.path.exists(output_file):
                os.remove(output_file)
            else:
                print("Failed to convert, keeping mp4 file.")
                
        if conversion_successful:
            print("Download complete.")


def sanitize_filename(filename):
    # Remove extra whitespace
    filename = " ".join(filename.split())
    
    # Remove invalid characters
    filename = re.sub(r'[\\/*?:"<>|]', "", filename)
    
    return filename


def console_print(string):
    try:
        print(f"{string.encode('utf-8', errors='ignore').decode('utf-8')}")
    except UnicodeEncodeError:
        encoding = locale.getpreferredencoding()
        print(f"{string.encode(encoding, errors='ignore').decode(encoding)}")
    except Exception as e:
        print(f"An error occurred while printing to the console: {e}")


def main():
    token = get_token()
    playlists = get_playlists(user_id, token)
    
    print("\nPlaylists:\n")
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
    # print(playlist_id)
    
    playlist_name = str(playlists[0][0])
    sanitized_playlist_name = sanitize_filename(playlist_name)
    
    chosen_playlist_print_string = f"Chosen playlist: {playlist_name}"
    console_print(chosen_playlist_print_string)
    
    # Create a directory with the name of the playlist in the downloads directory, if it doesn't already exist
    if not os.path.exists(os.path.join(downloads_dir, sanitized_playlist_name)):
        os.makedirs(os.path.join(downloads_dir, sanitized_playlist_name))
        print("Playlist directory created.\n")
    else:
        print("Playlist directory already exists.\n")
    
    existing_tracks = get_existing_tracks(sanitized_playlist_name)
    
    # print("Existing tracks: ")
    # for track in existing_tracks:
    #     try:
    #         print(f"{track.encode('utf-8', errors='ignore').decode('utf-8')}")
    #     except UnicodeEncodeError:
    #         encoding = locale.getpreferredencoding()
    #         print(f"{track.encode(encoding, errors='ignore').decode(encoding)}")
    
    print(f"Number of existing tracks: {len(existing_tracks)}")
    print()
    
    print("Downloading songs...")
    tracks_not_found, number_of_downloads, number_of_skips = get_tracks(playlist_id, token, existing_tracks, sanitized_playlist_name)
    
    print("\nAll downloads complete.")
    
    print(f"\nTracks downloaded: {number_of_downloads}")
    print(f"Tracks skipped (Already downloaded): {number_of_skips}")
    
    print()
    
    if len(tracks_not_found) == 0:
        print("All tracks found.")
    else:
        print("Tracks not found:\n")
        for track in tracks_not_found:
            console_print(track)

main()
