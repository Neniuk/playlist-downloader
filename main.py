from spotify_api import SpotifyAPI

from utils import Utils

def main():
    spotify_api = SpotifyAPI()
    utils = Utils()
    
    token = spotify_api.get_token()
    playlists = spotify_api.get_playlists(token)
    
    print("\nPlaylists:\n")
    i = 0
    for playlist in playlists:
        print(f"{i}. {playlist[0]}")
        i += 1
        
    print()
    
    playlist_index = input("Please enter the index of the playlist you wish to download: ")
    if playlist_index.isdigit():
        playlist_int_index = int(playlist_index)
        if playlist_int_index < 0 or playlist_int_index >= len(playlists):
            print("Invalid index.")
            return
    else:
        print("Invalid index.")
        return
    
    playlist_id = str(playlists[playlist_int_index][1])
    # print(playlist_id)
    
    playlist_name = str(playlists[playlist_int_index][0])
    sanitized_playlist_name = utils.sanitize_filename(playlist_name)
    
    chosen_playlist_string = f"Chosen playlist: {playlist_name}"
    utils.console_print(chosen_playlist_string)

    utils.create_playlist_directory(sanitized_playlist_name)
    
    existing_tracks = utils.get_existing_tracks(sanitized_playlist_name)
    # print("Existing tracks: ")
    # for track in existing_tracks:
    #     utils.console_print(track)
    
    print(f"Number of existing tracks: {len(existing_tracks)}")
    print()
    
    print("Downloading songs...")
    tracks_not_found, number_of_downloads, number_of_skips = spotify_api.get_tracks(playlist_id, token, existing_tracks, sanitized_playlist_name)
    
    print("\nAll downloads complete.")
    
    print(f"\nTracks downloaded: {number_of_downloads}")
    print(f"Tracks skipped (Already downloaded): {number_of_skips}")
    
    print()
    
    if len(tracks_not_found) == 0:
        print("All tracks found.")
    else:
        print("Tracks not found:\n")
        for track in tracks_not_found:
            utils.console_print(track)


main()

