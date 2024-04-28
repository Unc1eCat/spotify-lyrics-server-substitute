from collections import namedtuple
import gzip
import json
import re
from http.server import BaseHTTPRequestHandler
import socket
from typing import Iterable
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from spotify_lyrics_server_substitute.lyrics_backends.lyrics_backend import LyricsBackendBase
from spotify_lyrics_server_substitute import spotify_api

LYRICS_URL_PATTERN = re.compile(r"track\/([a-zA-Z0-9]+)\/image/(?:([a-zA-Z0-9_\/\?\=\&\:\.\-\#])\?)?")

ParsedRequest = namedtuple('ParsedRequest', 'track_id image_url')


class LyricsRequestHandler(BaseHTTPRequestHandler):
    backends: list[LyricsBackendBase]

    @staticmethod
    def as_class(backends: Iterable[LyricsBackendBase]):
        return type('LyricsRequestHandlerSub', (LyricsRequestHandler,), {
            'backends': backends
        })

    def assert_factory_used(self):
        ''' Checks that the client does not directly use `LyricsRequestHandler` class and instead has called `as_class` static factory. '''
        assert self.__class__.__name__ == 'LyricsRequestHandlerSub', "You can't use `LyricsRequestHandler class directly, please use `LyricsRequestHandler.as_class` static factory."

    # TODO: Make a strategy for this method. Turns out forwarding HTTP requests is not as easy as I thought
    def forward_to_real_server(self):
        ''' Sends the received request to real Spotify servers and sends the response they give back to the client app. '''
        # TODO: Rewrite it. Make it use TLS sockets and send contents of `self.rfile` through them to the real servers
        url = 'https://%s' % (self.headers['host'] + self.path,)
        content_length = int(self.headers.get('Content-Length', 0))
        req = Request(url, data=self.rfile.read(content_length), headers=dict(self.headers), method=self.command.upper())
        try:
            with urlopen(req) as res:
                self.send_response(res.code)
                for k, v in dict(res.headers).items():
                    self.send_header(k, v)
                # self.send_header('Content-Length', len(r := res.read()))
                self.end_headers()
                # content_length = int(res.headers.get('Content-Length', 0))
                # print(gzip.decompress(res.read()))
                # self.write(r)
                self.wfile.write(res.read(content_length) if content_length else res.read())
        except HTTPError as e:
            self.send_error(e.getcode(), e.reason)

    def extract_from_request(self):
        ''' Returns only the information we need from the request or None if the request should be forwarded to the real Spotify servers. '''
        try:
            return None
            match = LYRICS_URL_PATTERN.search(self.path)
            return ParsedRequest(match[1], match[2])
        except (IndexError, TypeError):
            return None

    def do_GET(self):
        self.assert_factory_used()

        req = self.extract_from_request()
        if not req:
            self.forward_to_real_server()
            return

        for i in self.backends:
            if lyrics := i.get_lyrics(req.track_id):
                break
        else:  # None of the backends found lyrics
            ...
            return
        # A backend found lyrics

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(spotify_api.make_response_body(lyrics, 'en', False, 0, -1, -1)).encode('latin-1'))
