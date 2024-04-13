from urllib.request import urlopen, Request
from urllib.parse import urlencode, quote
from bs4 import BeautifulSoup
import json

from src.lyrics_backends.lyrics_backend import LyricsBackendBase

GENIUS_URL_SEARCH = 'https://api.genius.com/search?q=%s'


class GeniusLyricsBackend(LyricsBackendBase):
    def __init__(self, app_client_id, app_client_secret, app_client_token) -> None:
        super().__init__()

        self.app_client_id = app_client_id
        self.app_client_secret = app_client_secret
        self.app_client_token = app_client_token

    def search_song(self, query: str):
        req = Request(GENIUS_URL_SEARCH % (quote(query, safe=''),))
        req.add_header('Authorization', 'Bearer ' + self.app_client_token)
        with urlopen(req) as res:
            return json.loads(res.read())

    def get_lyrics(self, genius_song_url: str):
        with urlopen(genius_song_url) as res:
            html = BeautifulSoup(res.read(), "html.parser")
            for i in html('script'):
                i.extract() 
            return html.find('div', class_='lyrics').get_text()
