import os
import time

from youtubesearchpython import VideosSearch
from yt_dlp import YoutubeDL
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB

from utils import Utils, Logger


class YoutubeAPI:
    def __init__(self):
        self.downloads_dir = os.getenv("DOWNLOADS_DIR")

    @staticmethod
    def get_video_url(song_name):
        videos_search = VideosSearch(song_name, limit=1)
        result = videos_search.result()

        if (
            not isinstance(result, dict) or
            "result" not in result or
            not isinstance(result["result"], list) or
            len(result["result"]) == 0
        ):
            return None, None

        video_info = result["result"][0]
        if (
            not isinstance(video_info, dict) or
            "link" not in video_info or
            "title" not in video_info
        ):
            return None, None

        video_url = result["result"][0]["link"]
        video_title = result["result"][0]["title"]

        return video_url, video_title

    @staticmethod
    def add_metadata(mp3_file, metadata):
        audio = MP3(mp3_file, ID3=ID3)

        if metadata["cover_art"] is not None:
            audio.tags.add(
                APIC(
                    encoding=3,
                    mime='image/jpeg',
                    type=3,
                    desc='Cover',
                    data=metadata["cover_art"]
                )
            )

        audio.tags.add(
            TIT2(
                encoding=3,
                text=metadata["title"]
            )
        )

        audio.tags.add(
            TPE1(
                encoding=3,
                text=metadata["artist"]
            )
        )

        audio.tags.add(
            TALB(
                encoding=3,
                text=metadata["album"]
            )
        )

        audio.save()

    def download_song(self, video_url, song_title, playlist_name):
        mp3_file = None

        song_title = Utils.sanitize_filename(song_title)
        output_path = os.path.join(self.downloads_dir, playlist_name)
        output_template = os.path.join(output_path, song_title + ".%(ext)s")

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'logger': Logger(),
            "quiet": True,
        }

        # Retry up to 3 times
        for _ in range(3):
            try:
                with YoutubeDL(ydl_opts) as ydl:
                    error_code = ydl.download([video_url])
                    if error_code != 0:
                        print(
                            f"Failed to download {song_title} ( {video_url} ) with error code {error_code}")
                        return None
                mp3_file = output_template.replace('.%(ext)s', '.mp3')
                break
            except Exception as e:
                print(
                    f"Failed to download {song_title} ( {video_url} ) with error: {e}")
                time.sleep(1)

        if mp3_file is None:
            print(
                f"Failed to download {song_title} ( {video_url} ) after 3 retries.")
            return None

        return mp3_file

    def download_song_wrapper(self, _video_title, video_url, playlist_name, metadata):
        try:
            mp3_file = self.download_song(
                video_url, metadata["title"], playlist_name)

            if mp3_file is None:
                return

            self.add_metadata(mp3_file, metadata)
        except Exception as e:
            print(f"An error occurred: {e}")
