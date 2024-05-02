from collections import namedtuple
import gzip
from http import HTTPStatus
import json
import re
from http.server import BaseHTTPRequestHandler
import socket
from typing import Iterable
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from spotify_lyrics_server_substitute.lyrics_backends.lyrics_backend import LyricsBackendBase
from spotify_lyrics_server_substitute import spotify_api
from src.spotify_api import parse_lyrics_request_url

HOP_BY_HOP_HEADERS = [i.lower() for i in ('Keep-Alive', 'Transfer-Encoding', 'TE', 'Connection', 'Trailer', 'Upgrade', 'Proxy-Authorization', 'Proxy-Authenticate')]


class LyricsRequestHandler(BaseHTTPRequestHandler):
    backend: LyricsBackendBase

    @staticmethod
    def as_class(backend: LyricsBackendBase):
        return type('LyricsRequestHandlerSub', (LyricsRequestHandler,), {
            'backend': backend
        })

    def assert_factory_used(self):
        ''' Checks that the client does not directly use `LyricsRequestHandler` class and instead has called `as_class` static factory. '''
        assert self.__class__.__name__ == 'LyricsRequestHandlerSub', "You can't use `LyricsRequestHandler class directly, please use `LyricsRequestHandler.as_class` static factory."

    def forward_to_real_server(self):
        ''' Sends the received request to real Spotify servers and sends the response they give back to the client app. '''
        # TODO: Those CONNECT request and keep-alives are blowin my mind up
        url = 'https://%s' % ((self.headers['host'] if self.path.startswith('/') else '') + self.path,)
        content_length = int(self.headers.get('Content-Length', 0))
        headers = {k.lower(): v for k, v in self.headers.items()}
        headers['connection'] = 'close'
        req = Request(url, data=self.rfile.read(content_length), headers=headers, method=self.command.upper())
        try:
            with urlopen(req) as res:
                self.send_response(res.code)
                for k, v in dict(res.headers).items():
                    if k.lower() not in HOP_BY_HOP_HEADERS:
                        self.send_header(k, v)
                self.send_header('Connection', 'close')
                r = res.read()
                if 'content-length' not in res.headers:
                    self.send_header('Content-Length', len(r))
                self.end_headers()
                self.wfile.write(r)
        except HTTPError as e:
            self.send_error(e.getcode(), e.reason)

    def handle_one_request(self) -> None:
        self.assert_factory_used()
        try:  # Copied straight out of superclass's `handle_one_request`
            self.raw_requestline = self.rfile.readline(65537)
            if len(self.raw_requestline) > 65536:
                self.requestline = ''
                self.request_version = ''
                self.command = ''
                self.send_error(HTTPStatus.REQUEST_URI_TOO_LONG)
                return
            if not self.raw_requestline:
                self.close_connection = True
                return
            if not self.parse_request():
                # An error code has been sent, just exit
                return

            self.req = parse_lyrics_request_url(self.path)
            if self.req:
                self.do()
            else:
                self.forward_to_real_server()
                return
            self.wfile.flush()  # actually send the response if not already done.
        except TimeoutError as e:
            # a read or a write timed out.  Discard this connection
            self.log_error("Request timed out: %r", e)
            self.close_connection = True
            return

    def do(self):
        lyrics = self.backend.get_lyrics(self.req.track_id)
        if lyrics:
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(lyrics.to_json()).encode('latin-1'))
        else:
            self.send_error(HTTPStatus.NOT_FOUND, 'No lyrics were found.')
