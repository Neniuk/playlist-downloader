from spotify_api import SpotifyAPI
from utils import Utils


def display_playlists(playlists):
    playlists.sort(key=lambda name: name[0].lower())
    print("\nPlaylists:\n")
    for i, playlist in enumerate(playlists):
        print(f"{i}. {playlist[0]}")
    print()


def get_playlist_index(playlists):
    playlist_index = input(
        "Please enter the index of the playlist you wish to download: ")
    if playlist_index.isdigit():
        playlist_int_index = int(playlist_index)
        if 0 <= playlist_int_index < len(playlists):
            return playlist_int_index
    print("Invalid index.")
    return None


def main():
    # Initialize classes
    spotify_api = SpotifyAPI()
    utils = Utils()

    # Get user auth, token & playlists
    spotify_api.get_user_auth()
    token = spotify_api.get_token()
    playlists = spotify_api.get_playlists(token)

    # Display playlists
    display_playlists(playlists)
    playlist_index = get_playlist_index(playlists)
    if playlist_index is None:
        return

    # Get playlist ID & name from chosen playlist, sanitize playlist name
    playlist_id = str(playlists[playlist_index][1])
    playlist_name = str(playlists[playlist_index][0])
    sanitized_playlist_name = utils.sanitize_filename(playlist_name)

    # Print chosen playlist
    chosen_playlist_string = f"\nChosen playlist: {playlist_name}"
    utils.console_print(chosen_playlist_string)

    # Create playlist directory & get existing tracks
    utils.create_playlist_directory(sanitized_playlist_name)
    existing_tracks = utils.get_existing_tracks(sanitized_playlist_name)

    # Get tracks from chosen playlist
    print(f"Number of existing tracks: {len(existing_tracks)}\n")
    print("Downloading tracks...")

    tracks_not_found, number_of_downloads, number_of_skips = spotify_api.get_tracks(
        playlist_id, token, existing_tracks, sanitized_playlist_name)

    print("\nAll downloads complete.")
    print(f"\nTracks downloaded: {number_of_downloads}")
    print(f"Tracks skipped (Already downloaded): {number_of_skips}\n")

    if not tracks_not_found:
        print("All tracks found.")
    else:
        print(f"Tracks not found ({len(tracks_not_found)}):")
        for track in tracks_not_found:
            utils.console_print(track)


if __name__ == "__main__":
    main()
