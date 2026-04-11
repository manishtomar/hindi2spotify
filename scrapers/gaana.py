import json
import logging
import re
from typing import List

import requests
from bs4 import BeautifulSoup

from scrapers import Song

logger = logging.getLogger(__name__)

PLAYLIST_URL = "https://gaana.com/playlist/gaana-dj-hindi-top-50-1"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
}


def get_songs(limit: int = 50) -> List[Song]:
    """Fetch trending Hindi songs from Gaana's Hindi Top 50 playlist."""
    try:
        resp = requests.get(PLAYLIST_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.error("Gaana request failed: %s", e)
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    scripts = soup.find_all("script")
    redux_script = next(
        (s.string for s in scripts if s.string and "REDUX_DATA" in s.string), None
    )

    if not redux_script:
        logger.warning("Gaana: REDUX_DATA not found in page")
        return []

    m = re.search(r"window\.REDUX_DATA\s*=\s*(\{.*\})\s*;?\s*$", redux_script, re.DOTALL)
    if not m:
        logger.warning("Gaana: could not extract REDUX_DATA JSON")
        return []

    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        logger.error("Gaana: failed to parse REDUX_DATA: %s", e)
        return []

    tracks = (
        data.get("playlist", {})
        .get("playlistDetail", {})
        .get("tracks", [])
    )

    if not tracks:
        logger.warning("Gaana: no tracks found in playlist")
        return []

    songs: List[Song] = []
    for item in tracks:
        if not isinstance(item, dict):
            continue

        title = item.get("track_title", "")
        if not title:
            continue

        raw_artists = item.get("artist", [])
        if isinstance(raw_artists, list):
            artists = [a["name"] for a in raw_artists if isinstance(a, dict) and a.get("name")]
        else:
            artists = []
        if not artists:
            artists = ["Unknown"]

        seokey = item.get("seokey", "")
        source_url = f"https://gaana.com/song/{seokey}" if seokey else ""

        songs.append(
            Song(
                title=title,
                artists=artists,
                album=item.get("album_title", ""),
                source="gaana",
                source_id=str(item.get("track_id", "")),
                source_url=source_url,
            )
        )

    logger.info("Gaana: fetched %d songs", len(songs))
    return songs[:limit]
