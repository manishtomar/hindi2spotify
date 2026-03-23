import json
import logging
import os
from typing import Dict, List, Optional

from thefuzz import fuzz

from normalizer import create_cache_key, create_search_query, normalize_artist, normalize_title
from scrapers import Song

logger = logging.getLogger(__name__)

CACHE_FILE = os.path.join(os.path.dirname(__file__), "song_cache.json")
MATCH_THRESHOLD = 75


class SpotifyMatcher:
    def __init__(self, sp):
        self.sp = sp
        self.cache: Dict[str, Optional[str]] = self._load_cache()

    def _load_cache(self) -> Dict[str, Optional[str]]:
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                logger.warning("Cache file corrupt, starting fresh")
        return {}

    def _save_cache(self):
        with open(CACHE_FILE, "w") as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)

    def _score_result(self, song: Song, track: dict) -> float:
        """Score a Spotify track result against the source song (0-100)."""
        sp_title = track.get("name", "")
        sp_artists = [a["name"] for a in track.get("artists", [])]

        title_score = fuzz.ratio(normalize_title(song.title), normalize_title(sp_title))

        best_artist_score = 0
        for src_artist in song.artists:
            for sp_artist in sp_artists:
                score = fuzz.ratio(
                    normalize_artist(src_artist), normalize_artist(sp_artist)
                )
                best_artist_score = max(best_artist_score, score)

        return 0.7 * title_score + 0.3 * best_artist_score

    def match_song(self, song: Song) -> Optional[str]:
        """Match a song to a Spotify track URI. Returns URI or None."""
        cache_key = create_cache_key(song)

        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if cached:
                logger.debug("Cache hit: %s -> %s", song.title, cached)
            else:
                logger.debug("Cache hit (negative): %s", song.title)
            return cached

        query = create_search_query(song)
        try:
            results = self.sp.search(q=query, type="track", market="IN", limit=5)
        except Exception as e:
            logger.error("Spotify search failed for %r: %s", song.title, e)
            return None

        tracks = results.get("tracks", {}).get("items", [])
        if not tracks:
            logger.info("No Spotify results for: %s", song.title)
            self.cache[cache_key] = None
            return None

        best_track = None
        best_score = 0.0

        for track in tracks:
            score = self._score_result(song, track)
            if score > best_score:
                best_score = score
                best_track = track

        if best_score >= MATCH_THRESHOLD and best_track:
            uri = best_track["uri"]
            logger.info(
                "Matched: %s -> %s (score: %.1f)",
                song.title,
                best_track["name"],
                best_score,
            )
            self.cache[cache_key] = uri
            return uri

        logger.info(
            "No good match for %s (best score: %.1f)", song.title, best_score
        )
        self.cache[cache_key] = None
        return None

    def match_songs(self, songs: List[Song]) -> List[str]:
        """Match a list of songs, return list of Spotify URIs."""
        uris = []
        for song in songs:
            uri = self.match_song(song)
            if uri:
                uris.append(uri)
        self._save_cache()
        logger.info("Matched %d/%d songs", len(uris), len(songs))
        return uris
