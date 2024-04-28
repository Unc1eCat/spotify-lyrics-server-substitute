import re
from src.lyrics_backends.lyrics_backend import LyricsBackendBase
from spotify_lyrics_server_substitute.spotify_api import LyricsLine, NameArtists, SpotifyAPI
from functools import partial
from itertools import chain, combinations, product
from urllib.error import HTTPError
import editdistance as ed
from urllib.request import urlopen, Request
from urllib.parse import urlencode, quote
from bs4 import BeautifulSoup
import json

GENIUS_URL_SEARCH = 'https://api.genius.com/search?q=%s'
LYRICS_DIV_CLASS_PATTERN = re.compile("^lyrics$|Lyrics__Container")
NON_SANG_PATTERN = re.compile("\[.*?\]")
# SPOTIFY_READY_LYRICS = re.compile(...)  # TODO: Write the pattern. See the docstring, `get_lyrics`
'''
Verifies whether the lyrics look like they should in Spotify. In Spotify all lyrics are concise. They contain only words and numbers, special symbols are 
used only for punctuation imposed by the human language.  
'''

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
        req.add_header('Authorization', 'Bearer ' + self.genius_client_token)
        with urlopen(req) as res:
            return json.loads(res.read())

    # TODO: Checking that no hit is good enough
    def pick_best_hit(self, hits: list, name_artists: NameArtists):
        ''' Contains the algorithm for picking the single best matching search result from a bunch of them or confirming that none of the results are good. '''
        hits = [i for i in hits if i['type'] == 'song']  # Filter out anything that's not a song
        hits = hits[:self.number_take_matches]  # Take top n best matches

        def hit_score(hit):
            distance_to_primary_artist = partial(ed.eval, hit['result']['primary_artist']['name'])
            name_distance = ed.eval(hit['result']['title'], name_artists.name)
            artist_distance = distance_to_primary_artist(min(name_artists.artists, key=distance_to_primary_artist))
            return -(name_distance + artist_distance)
        return max(hits, key=hit_score)

    def scrape_lyrics_from_page(self, url):
        req = Request(url)
        req.add_header('User-Agent', 'https://github.com/Unc1eCat/spotify-lyrics-server-substitute')
        with urlopen(req) as res:
            html = BeautifulSoup(a := res.read(), "html.parser")
            for i in html('script'):
                i.extract()
            divs = html.find_all('div', class_=LYRICS_DIV_CLASS_PATTERN)
            for i in divs:
                for br in i.find_all('br'):
                    br.replace_with('\n')

            return '\n'.join(i.get_text() for i in divs).strip(' \n')

    def get_lyrics(self, spotify_track_id: str, remove_non_sang_text=False):
        ''' Returns lyrics from Genius for track with Spotify ID `spotify_track_id`. If `remove_non_sang_text` is true, removes genius thingies in square 
         brackets. '''
        name_artists = self.spotify.get_name_artists_by_id(spotify_track_id)
        hits = self.search_song(name_artists.name + ' - ' + ', '.join(name_artists.artists))['response']['hits']
        genius_track_url = self.pick_best_hit(hits, name_artists)['result']['url']

        lyrics = self.scrape_lyrics_from_page(genius_track_url).strip(' \n')
        if remove_non_sang_text:  # TODO: Improve the lyrics processing algorithm
            lyrics = NON_SANG_PATTERN.sub('', lyrics)
            lyrics = '\n'.join(i for i in lyrics.split('\n') if i)  # Remove excessive newlines
        return [LyricsLine(i, 0) for i in lyrics.split('\n')]

# TODO: REMOVE TEST API CLIENTS. THEY HAVE SECRET KEYS EXPOSED ON GITHUB
