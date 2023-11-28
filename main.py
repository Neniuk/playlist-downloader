from youtube_api import YoutubeAPI
from spotify_api import SpotifyAPI

from utils import Utils

def main():
    token = SpotifyAPI.get_token()
    playlists = SpotifyAPI.get_playlists(token)
    
    print("\nPlaylists:\n")
    i = 0
    for playlist in playlists:
        print(f"{i}. {playlist[0]}")
        i += 1
        
    print()
    
    # playlist_index = input("\nPlease enter the index of the playlist you wish to download: ")
    
    # if playlist_index.isdigit() and (int_index >= 0) and (int_index < playlists.len()):
    #     int_index = int(playlist_index)
    #     songs = get_songs(playlists[int_index][1])
    # else:
    #     print("Invalid index.")
    
    playlist_id = str(playlists[0][1])
    # print(playlist_id)
    
    playlist_name = str(playlists[0][0])
    sanitized_playlist_name = Utils.sanitize_filename(playlist_name)
    
    chosen_playlist_string = f"Chosen playlist: {playlist_name}"
    Utils.console_print(chosen_playlist_string)
    
    # Create a directory with the name of the playlist in the downloads directory, if it doesn't already exist
    Utils.create_playlist_directory(sanitized_playlist_name)
    
    existing_tracks = Utils.get_existing_tracks(sanitized_playlist_name)
    # print("Existing tracks: ")
    # for track in existing_tracks:
    #     Utils.console_print(track)
    
    print(f"Number of existing tracks: {len(existing_tracks)}")
    print()
    
    print("Downloading songs...")
    tracks_not_found, number_of_downloads, number_of_skips = SpotifyAPI.get_tracks(playlist_id, token, existing_tracks, sanitized_playlist_name)
    
    print("\nAll downloads complete.")
    
    print(f"\nTracks downloaded: {number_of_downloads}")
    print(f"Tracks skipped (Already downloaded): {number_of_skips}")
    
    print()
    
    if len(tracks_not_found) == 0:
        print("All tracks found.")
    else:
        print("Tracks not found:\n")
        for track in tracks_not_found:
            Utils.console_print(track)

main()
