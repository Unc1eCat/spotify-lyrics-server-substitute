
from collections import namedtuple
from typing import Iterable

from spotify_lyrics_server_substitute.spotify_api import LyricsLine, LyricsResponse

# TODO: Incorporate ABC. For now its just a reference on what to implement in the lyrics backend classes


class LyricsBackendBase:
    ''' Abstract class for all classes that are gonna provide a pythonic API for fetching lyrics and searching songs from a specific lyrics websites. '''

    def get_lyrics(self, spotify_track_id: str) -> LyricsResponse:
        ''' This method must either return valid lyrics or None if no good lyrics were found. If valid lyrics are returned they will be directly displayed
        in Spotify, no extra processing must and will take place outside of this method. '''
        raise NotImplementedError()


class SequentialMultiBackend(LyricsBackendBase):
    def __init__(self, backends: Iterable[LyricsBackendBase]) -> None:
        super().__init__()

        self.backends = backends

    def get_lyrics(self, spotify_track_id: str) -> Iterable[LyricsLine]:
        for i in self.backends:
            lyrics = i.get_lyrics()
            if lyrics:
                return lyrics
        else:
            return None
