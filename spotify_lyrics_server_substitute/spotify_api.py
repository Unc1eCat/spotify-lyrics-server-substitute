from collections import namedtuple
from dataclasses import dataclass
import json
from crypt import methods
import locale
import re
from typing import Iterable
from urllib.request import urlopen, Request
from urllib.parse import urlencode, parse_qs
import base64

SPOTIFY_URL_TOKEN = 'https://accounts.spotify.com/api/token'
SPOTIFY_URL_GET_TRACK = 'https://api.spotify.com/v1/tracks/%s'

LYRICS_URL_PATTERN = re.compile(r"track\/([a-zA-Z0-9]+)\/image/(?:([a-zA-Z0-9_\/\?\=\&\:\.\-\#])\?)?")

Color = int | tuple[4]
''' Int to put directly into response JSON or a tuple of 4 integer representing aRGb components (0 - 255)'''


def _convert_color(color: Color) -> int:
    assert isinstance(color, int) or (isinstance(color, tuple) and len(color) == 4 and all(0 <= i <= 255 for i in color))
    return color if isinstance(color, int) else int.from_bytes(bytes(color), 'big', signed=True)


LyricsLine = namedtuple('LyricsLine', 'words time_ms')
NameArtists = namedtuple('NameArtists', 'name artists')
ParsedRequest = namedtuple('ParsedRequest', 'track_id image_url')


def parse_lyrics_request_url(url, method = None):
    ''' Returns only the information we need from the request or None if the request should be forwarded to the real Spotify servers. If you provide `method`
     parameter then checks if it is an HTTP method that we should handle. '''
    if method not in ('GET', None):
        return None
    try:
        match = LYRICS_URL_PATTERN.search(url)
        return ParsedRequest(match[1], match[2])
    except (IndexError, TypeError):
        return None


@dataclass()
class LyricsResponse:
    ''' Encapsulates the response body to send back to the Spotify client. '''
    lyrics: Iterable[LyricsLine]
    language: str
    is_rtl_language: bool
    background_color: Color
    unhighlighted_text_color: Color
    highlighted_text_color: Color

    def to_json(self):
        lines = [
            {
                'startTimeMs': i.time_ms,
                'words': i.words,
                'syllables': [],
                'endTimeMs': '0'
            }
            for i in self.lyrics
        ]
        json = {
            'lyrics': {
                'lines': lines,
                'provider': 'LyricsServerSubstitute',
                'providerLyricsId': '0',  # TODO: Check if this field matters
                'providerDisplayName': 'Lyrics Server Substitute',
                'syncLyricsUri': '',
                'isDenseTypeface': False,
                'alternatives': [],
                'language': self.language,
                'isRtlLanguage': self.is_rtl_language,
                'fullscreenAction': 'FULLSCREEN_LYRICS',
                'showUpsell': False,
                'capStatus': 'NONE',
                'impressionsRemaining': 0,
            },
            'colors': {
                'background': _convert_color(self.background_color),
                'text': _convert_color(self.unhighlighted_text_color),
                'highlightText': _convert_color(self.highlighted_text_color)
            },
            'hasVocalsRemoval': False
        }
        return json


class SpotifyWebAPI:
    def __init__(self, app_client_id: str, app_client_secret: str):
        self.app_client_id = app_client_id
        self.app_client_secret = app_client_secret

        headers = {
            'Authorization': 'Basic ' + base64.b64encode(bytes(app_client_id + ':' + app_client_secret, 'utf-8')).decode('utf-8'),
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'grant_type': 'client_credentials'
        }

        res = urlopen(Request(SPOTIFY_URL_TOKEN, headers=headers, data=bytes(urlencode(data), 'utf-8'), method='POST'))
        self.access_token = json.loads(res.read())['access_token']

    def get_track_by_id(self, track_id: str):
        req = Request(SPOTIFY_URL_GET_TRACK % (track_id,))
        req.add_header('Authorization', 'Bearer ' + self.access_token)
        res = urlopen(req)
        return json.loads(res.read())

    def get_name_artists_by_id(self, track_id: str):
        json = self.get_track_by_id(track_id)
        return NameArtists(json['name'], [i['name'] for i in json['artists']])
