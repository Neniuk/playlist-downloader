import string
import secrets
import re
import locale
import os

class Utils:
    def __init__(self):
        self.downloads_dir = os.getenv("DOWNLOADS_DIR")


    def random_string(self, size):        
        letters = string.ascii_lowercase+string.ascii_uppercase+string.digits            
        return ''.join(secrets.choice(letters) for i in range(size))


    def sanitize_filename(self, filename):
        # Remove extra whitespace
        filename = " ".join(filename.split())
        
        # Remove invalid characters
        filename = re.sub(r'[\\/*?:"<>|]', "", filename)
        
        return filename


    def console_print(self, string):
        try:
            print(f"{string.encode('utf-8', errors='ignore').decode('utf-8')}")
        except UnicodeEncodeError:
            encoding = locale.getpreferredencoding()
            print(f"{string.encode(encoding, errors='ignore').decode(encoding)}")
        except Exception as e:
            print(f"An error occurred while printing to the console: {e}")


    def create_playlist_directory(self, sanitized_playlist_name):
        if not os.path.exists(os.path.join(self.downloads_dir, sanitized_playlist_name)):
            os.makedirs(os.path.join(self.downloads_dir, sanitized_playlist_name))
            print("Playlist directory created.\n")
        else:
            print("Playlist directory already exists.\n")


    def get_existing_tracks(self, playlist_name):
        existing_tracks = []
        for filename in os.listdir("./" + self.downloads_dir + "/" + playlist_name):
            if filename.endswith(".mp3"):
                existing_tracks.append(filename[:-4])
        
        return existing_tracks

