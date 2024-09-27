
# Playlist Downloader (CLI)

This project allows you to list your playlists on Spotify, and download the tracks from a chosen playlist.



## Installation

Ready built binaries are available on the [releases page](https://github.com/Neniuk/playlist-downloader/releases). There are both a Linux and Windows (*.exe) version available.


## Requirements

You need to have ffmpeg installed before running the program, it is used in order to get just the mp3 audio files of the downloaded videos.


## Usage/Examples

Before starting the application, you need to: 

1. Extract the archive (zip or tar.gz)
2. Rename the file '.env.sample' -> '.env'
3. Edit the file '.env' and change CLIENT_ID, CLIENT_SECRET & USER_ID to use your own. They can be found on Spotify Developer Dashboard, and on the Spotify User Profile
4. Finally you can start the application using one of the following commands (*.exe for Windows)

```bash
./pld
```
```bash
./pld.exe
```

5. You will be asked to open a link in your browser to authenticate the application with Spotify.

6. Now you can choose which playlist you want to download by typing the index of the playlist (the number of the list item, shown on the left side of the playlist name) you want to download and hitting enter in the terminal. You will be informed of the progress of the downloads.  

Note: Please do not touch the files in the specified download folder, nor move the folder in the middle of the download to avoid unexpected behavior.
