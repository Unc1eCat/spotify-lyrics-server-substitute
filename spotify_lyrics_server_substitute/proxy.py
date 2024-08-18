from http.server import BaseHTTPRequestHandler
from io import BytesIO
from socket import AF_INET, SOCK_STREAM, socket
from threading import Thread
from typing import Any, Tuple


class HttpParser:
    ''' Parses HTTP message from raw bytes '''
    def __init__(self, request_bytes) -> None:
        self.rfile = BytesIO(request_bytes)
        self.raw_requestline = self.rfile.readline()
        BaseHTTPRequestHandler.parse_request(self)

    def send_error(self, error_code, error_message, error_explain):
        self.error_code = error_code
        self.error_message = error_message
        self.error_explain = error_explain


class RequestHandler:
    ''' This class is run in a separate thread when the proxy accepts a connection from the Spotify client to handle the accepted socket. '''

    def __init__(self, socket, address) -> None:
        self.socket = socket
        self.address = address

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        pass


class Proxy:
    def __init__(self, address_port: Tuple[str, int] = ('localhost', 0)) -> None:
        self._server_socket = socket(AF_INET, SOCK_STREAM)
        self._server_socket.bind(address_port)
        self._server_socket.listen(5)
        self._acceptor_thread = Thread(target=self._run)
        self._acceptor_thread.start()

        self._handler_threads = []

    @property
    def port(self):
        return self._server_socket.getsockname()[1]

    def _run(self):
        while True:
            sock, addr = self._server_socket.accept()
            handler_thread = Thread(target=RequestHandler(sock, addr))
            handler_thread.start()
            self._handler_threads.append(handler_thread)
