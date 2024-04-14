from functools import partial
from itertools import combinations, product
import editdistance as ed
from urllib.request import urlopen, Request
from urllib.parse import urlencode, quote
from bs4 import BeautifulSoup
import json

from spotify_lyrics_server_substitute.spotify_api import NameArtists, SpotifyAPI
from src.lyrics_backends.lyrics_backend import LyricsBackendBase

GENIUS_URL_SEARCH = 'https://api.genius.com/search?q=%s'


# TODO: Add exception handling and error checking
class GeniusLyricsBackend(LyricsBackendBase):
    def __init__(self, genius_client_token: str, spotify: SpotifyAPI, *, number_take_matches=10) -> None:
        super().__init__()

        # self.app_client_id = app_client_id
        # self.app_client_secret = app_client_secret
        self.number_take_matches = number_take_matches
        self.spotify = spotify
        self.genius_client_token = genius_client_token

    def search_song(self, query: str):
        ''' Returns API call result in JSON '''
        req = Request(GENIUS_URL_SEARCH % (quote(query, safe=''),))
        req.add_header('Authorization', 'Bearer ' + self.app_client_token)
        with urlopen(req) as res:
            return json.loads(res.read())

    def pick_best_hit(self, hits: list, name_artists: NameArtists):
        ''' Contains the algorithm for picking the single best matching search result from a bunch of them or saying that none of the results are good. '''
        hits = (i for i in hits if i['type'] == 'song')  # Filter out anything that's not a song
        hits = hits[:self.number_take_matches]  # Take top n best matches

        def hit_score(hit):
            distance_to_primary_artist = partial(ed.eval, hit['result']['primary_artist']['name'])
            name_distance = ed.eval(hit['result']['title'], name_artists.name)
            artist_distance = distance_to_primary_artist(min(name_artists.artists, key=distance_to_primary_artist))
            return -(name_distance + artist_distance)
        return max(hits, key=hit_score)

    def scrape_lyrics_from_page(self, url):        
        with urlopen(url) as res:
            html = BeautifulSoup(res.read(), "html.parser")
            for i in html('script'):
                i.extract()
            return html.find('div', class_='lyrics').get_text()

    def get_lyrics(self, spotify_track_id: str):
        name_artists = self.spotify.get_name_artists_by_id(spotify_track_id)
        hits = self.search_song(name_artists.name + ' - ' + ', '.join(name_artists.artists))['response']['hits']
        genius_track_url = self.pick_best_hit(hits, name_artists)['result']['url']
        return self.scrape_lyrics_from_webpage(genius_track_url)