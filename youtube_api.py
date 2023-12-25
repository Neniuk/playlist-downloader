import os
import subprocess
import time
import http.client
from youtubesearchpython import VideosSearch
from pytube import YouTube
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB

from utils import Utils


class YoutubeAPI:
    def __init__(self):
        self.downloads_dir = os.getenv("DOWNLOADS_DIR")
        self.keep_mp4_without_ffmpeg = os.getenv("KEEP_MP4_WITHOUT_FFMPEG")

    def get_video_url(self, song_name):
        videosSearch = VideosSearch(song_name, limit=1)
        result = videosSearch.result()

        if result["result"] == []:
            return None

        video_url = result["result"][0]["link"]

        return video_url

    def get_audio_stream(self, video_url, song_title, playlist_name):
        output_file = None
        mp3_file = None

        yt = YouTube(video_url)

        download_print_string = f"\nDownloading: {yt.title}"
        Utils.console_print(download_print_string)

        # Retry up to 3 times
        for _ in range(3):
            try:
                audio = yt.streams.filter(only_audio=True).first()
                break
            except http.client.IncompleteRead:
                time.sleep(1)
        else:
            print("Failed to download audio stream after 3 attempts")
            audio = None

        song_title = Utils.sanitize_filename(song_title)

        # Retry up to 3 times
        for _ in range(3):
            try:
                output_file = audio.download(output_path=os.path.join(
                    self.downloads_dir, playlist_name), filename=song_title + ".mp4")
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
            return None, None

        mp3_file = os.path.splitext(output_file)[0] + '.mp3'
        # print("MP3 FILE:" + mp3_file)

        return output_file, mp3_file

    def add_metadata(self, mp3_file, metadata):
        audio = MP3(mp3_file, ID3=ID3)

        if (metadata["cover_art"] is not None):
            audio.tags.add(
                APIC(
                    encoding=3,
                    mime='image/jpeg',
                    type=3,
                    desc=u'Cover',
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

    def cleanup_mp4(self, output_file, conversion_successful):
        if self.keep_mp4_without_ffmpeg == "0" and os.path.exists(output_file):
            os.remove(output_file)
        else:
            if conversion_successful and os.path.exists(output_file):
                os.remove(output_file)
            else:
                print("Failed to convert, keeping mp4 file.")

    def convert_to_mp3(self, output_file, mp3_file, metadata):
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
            if conversion_successful and os.path.exists(mp3_file):
                print("Adding track metadata...")
                self.add_metadata(mp3_file, metadata)

            self.cleanup_mp4(output_file, conversion_successful)

            if conversion_successful:
                print("Download complete.")

    def download_song(self, video_url, playlist_name, metadata):
        output_file, mp3_file = self.get_audio_stream(
            video_url, metadata["title"], playlist_name)

        if output_file is None:
            return

        self.convert_to_mp3(output_file, mp3_file, metadata)
