import os
from typing import List, Tuple
from proxy.http.parser import HttpParser
from proxy.http.proxy import HttpProxyBasePlugin
from proxy.http.server import HttpWebServerBasePlugin, httpProtocolTypes
from proxy.http import responses

from spotify_lyrics_server_substitute import spotify_api
from spotify_lyrics_server_substitute.lyrics_backends.genius import GeniusLyricsBackend
from spotify_lyrics_server_substitute.spotify_api import LYRICS_REQUEST_HOSTNAME, LYRICS_REQUEST_PATH_START, SpotifyWebAPI

GENIUS_CLIENT_TOKEN = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')


class ServerPlugin(HttpWebServerBasePlugin):
    available_routes = (
        (httpProtocolTypes.HTTP, r'/color-lyrics/v2/track'),
        (httpProtocolTypes.HTTPS, r'/color-lyrics/v2/track'),
    )

    backends = (
        GeniusLyricsBackend(GENIUS_CLIENT_TOKEN, SpotifyWebAPI(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)),
    )

    def routes(self) -> List[Tuple[int, str]]:
        return self.available_routes

    def handle_request(self, request: HttpParser) -> None:
        print('SLAAAAAAAAAAAAAAAAY')
        p = spotify_api.parse_lyrics_request_url(request.path)
        for i in self.backends:
            res = i.get_lyrics(123).to_json(p.track_id)
            if res:
                self.client.queue(responses.okResponse(content=''.join(res.lyrics).encode()))
                break
        else:
            # TODO: Find out what the real Spotify servers respond with when they can't find lyrics
            self.client.queue(responses.NOT_FOUND_RESPONSE_PKT)


class ProxyPlugin(HttpProxyBasePlugin):
    lyrics_request_hostname = LYRICS_REQUEST_HOSTNAME.strip('/').encode()
    lyrics_request_path_start = LYRICS_REQUEST_PATH_START.strip('/').encode()

    def before_upstream_connection(self, request: HttpParser) -> HttpParser | None:
        print('------ UPSTREAM 1 ------')
        print(request.build().decode())
        print('-----------------------')

        if request.host == self.lyrics_request_hostname and (request.is_https_tunnel or request.path.strip(b'/').startswith(self.lyrics_request_path_start)):
            request.host = 'localhost'
            request.port = 8899
            if request.has_header(b'host'):
                request.del_header(b'host')
                request.add_header(b'host', b'localhost:8899')

        print('------ UPSTREAM 2 ------')
        print(request.build().decode())
        print('-----------------------')

        return request
