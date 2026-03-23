from dataclasses import dataclass, field
from typing import List


@dataclass
class Song:
    title: str
    artists: List[str]
    album: str = ""
    source: str = ""
    source_id: str = ""
    source_url: str = ""

    def _key(self):
        return (
            self.title.strip().lower(),
            tuple(sorted(a.strip().lower() for a in self.artists)),
        )

    def __hash__(self):
        return hash(self._key())

    def __eq__(self, other):
        if not isinstance(other, Song):
            return NotImplemented
        return self._key() == other._key()

    def __repr__(self):
        artists = ", ".join(self.artists)
        return f"Song({self.title!r} by {artists})"
