import re
from http.server import BaseHTTPRequestHandler

from spotify_api import SpotifyAPI

LYRICS_URL_TRACK_PART = re.compile(r"track/([a-zA-Z0-9]+)/image")


def lyrics_request_handler_class_factory(spotify_api: str): # Used to DI things into the request handler 
    return type('LyricsRequestHandler', (_LyricsRequestHandlerBase,), {"spotify_api": spotify_api})

class _LyricsRequestHandlerBase(BaseHTTPRequestHandler):
    spotify_api: SpotifyAPI

    def get_track_id(self):
        try:
            return LYRICS_URL_TRACK_PART.search(self.path)[0]
        except IndexError:
            print("A request was received from the Spotify client that cannot be handled.")
            raise

    def do_GET(self):
        track_id = self.get_track_id()

