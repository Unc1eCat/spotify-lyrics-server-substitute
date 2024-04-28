
from collections import namedtuple
from typing import Iterable

from spotify_lyrics_server_substitute.spotify_api import LyricsLine

# TODO: Incorporate ABC. For now its just a reference on what to implement in the lyrics backend classes
class LyricsBackendBase:
    ''' Abstract class for all classes that are gonna provide a pythonic API for fetching lyrics and searching songs from a specific lyrics websites. '''

    def get_lyrics(self, spotify_track_id: str) -> Iterable[LyricsLine]:
        ''' This method must either return valid lyrics or None if no good lyrics were found. If valid lyrics are returned they will be directly displayed
        in Spotify, no extra processing must and will take place outside of this method. The lyrics must be returned in the format of an iterable of `LyricsLine` 
        elements, where every `LyricsLine` element represents one single line of text to be displayed on lyrics page in Spotify. '''
        raise NotImplementedError()
