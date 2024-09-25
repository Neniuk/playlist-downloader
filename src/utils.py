import string
import secrets
import re
import locale
import os
import logging


class Logger:
    def __init__(self):
        # Set up the logger
        self.log = logging.getLogger()
        # Set to INFO to reduce verbosity
        self.log.setLevel(logging.ERROR)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'))
        self.log.addHandler(handler)

    def debug(self, msg):
        self.log.debug(msg)

    def info(self, msg):
        self.log.info(msg)

    def warning(self, msg):
        self.log.warning(msg)

    def error(self, msg):
        self.log.error(msg)


class Utils:
    def __init__(self):
        self.downloads_dir = os.getenv("DOWNLOADS_DIR")

    @staticmethod
    def random_string(size):
        letters = string.ascii_letters + string.digits
        return ''.join(secrets.choice(letters) for _ in range(size))

    @staticmethod
    def sanitize_filename(filename):
        # Remove extra whitespace & invalid characters
        filename = " ".join(filename.split())
        filename = re.sub(r'[\\/*?:"<>|]', "", filename)
        return filename

    @staticmethod
    def console_print(message):
        try:
            print(f"{message.encode('utf-8', errors='ignore').decode('utf-8')}")
        except UnicodeEncodeError:
            encoding = locale.getpreferredencoding()
            print(f"{message.encode(encoding, errors='ignore').decode(encoding)}")
        except Exception as e:
            print(f"An error occurred while printing to the console: {e}")

    def create_playlist_directory(self, sanitized_playlist_name):
        path = os.path.join(self.downloads_dir, sanitized_playlist_name)
        if not os.path.exists(path):
            os.makedirs(path)
            print("Playlist directory created.\n")
        else:
            print("Playlist directory already exists.\n")

    def get_existing_tracks(self, playlist_name):
        path = os.path.join(self.downloads_dir, playlist_name)
        return [filename[:-4] for filename in os.listdir(path) if filename.endswith(".mp3")]
