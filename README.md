# Playlist Downloader (CLI)

## Dependencies

-   [ffmpeg](https://ffmpeg.org/) (Optional, but HIGHLY recommended)

-   Used to convert the downloaded .mp4 files to .mp3

## Quick Start

### Usage

#### Downloading a playlist

In order to download a playlist, you must first add your Spotify API credentials and your Spotify username to the "config.json" file. You can get your Spotify API credentials [here](https://developer.spotify.com/dashboard/applications). Your Spotify username is the name that appears at the top of the Spotify app. By default playlists are downloaded to a "Downloads" folder in the same directory as the main program. You can change this by changing the "download_path" variable in the "config.json" file. Once you have added your credentials and username, you can run the following command to download a playlist:

`python3 main.py`

The program will then list all of the playlists associated with your account. You can then enter the number of the playlist you want to download. The program will then download the playlist to the "download_path" specified in the "config.json" file. The playlist will be located in a folder of the same name as the playlist.

##### Converting to .mp3

If you have ffmpeg installed and set up on the path, the program will convert the downloaded .mp4 files to .mp3 files automatically. If you do not have ffmpeg installed or set up correctly on the path, the program will not convert the files and will leave them as .mp4 files (they will still only have the audio stream).

After converting the files to .mp3, the program will add almbum art, and other related metadata to the .mp3 files.
