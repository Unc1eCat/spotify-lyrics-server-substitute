from collections import namedtuple
import json
from crypt import methods
from urllib.request import urlopen, Request
from urllib.parse import urlencode, parse_qs
import base64


SPOTIFY_URL_TOKEN = 'https://accounts.spotify.com/api/token'
SPOTIFY_URL_GET_TRACK = 'https://api.spotify.com/v1/tracks/%s'


NameArtists = namedtuple('NameArtists', 'name artists')


class SpotifyAPI:
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


    