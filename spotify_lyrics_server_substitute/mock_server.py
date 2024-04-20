import json
import re
from http.server import BaseHTTPRequestHandler

from spotify_lyrics_server_substitute.lyrics_backends.lyrics_backend import LyricsBackendBase
from spotify_lyrics_server_substitute import spotify_api

LYRICS_URL_TRACK_PART = re.compile(r"track/([a-zA-Z0-9]+)/image")


class LyricsRequestHandler(BaseHTTPRequestHandler):
    backends: list[LyricsBackendBase]

    @staticmethod
    def as_class(backends: list[LyricsBackendBase]):
        return type('LyricsRequestHandlerSub', (LyricsRequestHandler,), {
            'backends': backends
        })

    def assert_factory_used(self):
        assert self.__class__.__name__ == 'LyricsRequestHandlerSub', "You can't use `LyricsRequestHandler class directly, please use `LyricsRequestHandler.as_class` static factory."

    def get_track_id(self):
        try:
            return LYRICS_URL_TRACK_PART.search(self.path)[1]
        except (IndexError, AttributeError):
            print("A request was received from the Spotify client that cannot be handled.")
            raise

    def do_GET(self):
        self.assert_factory_used()

        track_id = self.get_track_id()
        for i in self.backends:
            if lyrics := i.get_lyrics(track_id):
                break
        else:  # None of the backends found lyrics
            ...
        # A backend found lyrics

        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps(spotify_api.make_response_body(lyrics)))
