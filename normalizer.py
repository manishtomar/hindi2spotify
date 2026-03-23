import re

from scrapers import Song

# Patterns to strip from titles
_PAREN_RE = re.compile(r"\s*[\(\[\{].*?[\)\]\}]\s*")
_FEAT_RE = re.compile(r"\s*(feat\.?|ft\.?|with)\s+.*", re.IGNORECASE)
_TAGS_RE = re.compile(
    r"\s*[-–—]?\s*(official\s*(music\s*)?video|lyric(al)?\s*video|audio|"
    r"visuali[sz]er|remix|reprise|unplugged|acoustic)\s*$",
    re.IGNORECASE,
)
_MULTI_SPACE_RE = re.compile(r"\s+")


def normalize_title(title: str) -> str:
    """Clean a song title for matching."""
    title = _PAREN_RE.sub(" ", title)
    title = _FEAT_RE.sub("", title)
    title = _TAGS_RE.sub("", title)
    title = _MULTI_SPACE_RE.sub(" ", title).strip().lower()
    return title


def normalize_artist(artist: str) -> str:
    """Clean an artist name for matching."""
    artist = _PAREN_RE.sub(" ", artist)
    artist = _MULTI_SPACE_RE.sub(" ", artist).strip().lower()
    return artist


def create_cache_key(song: Song) -> str:
    """Create a normalized cache key from a song."""
    title = normalize_title(song.title)
    artists = ",".join(sorted(normalize_artist(a) for a in song.artists))
    return f"{title}::{artists}"


def create_search_query(song: Song) -> str:
    """Build a Spotify search query from a song."""
    title = normalize_title(song.title)
    primary_artist = normalize_artist(song.artists[0]) if song.artists else ""
    if primary_artist:
        return f"track:{title} artist:{primary_artist}"
    return f"track:{title}"
