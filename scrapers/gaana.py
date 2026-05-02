import json
import logging
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
    # Gaana embeds a JSON-LD MusicPlaylist schema block containing all tracks
    playlist_script = next(
        (s.string for s in soup.find_all("script", type="application/ld+json")
         if s.string and '"MusicPlaylist"' in s.string),
        None,
    )

    if not playlist_script:
        logger.warning("Gaana: MusicPlaylist JSON-LD not found in page")
        return []

    try:
        data = json.loads(playlist_script)
    except json.JSONDecodeError as e:
        logger.error("Gaana: failed to parse JSON-LD: %s", e)
        return []

    tracks = data.get("track", [])

    if not tracks:
        logger.warning("Gaana: no tracks found in playlist")
        return []

    songs: List[Song] = []
    for item in tracks:
        if not isinstance(item, dict):
            continue

        title = item.get("name", "")
        if not title:
            continue

        raw_artist = item.get("byArtist", {}).get("name", "")
        artists = [a.strip() for a in raw_artist.split(",") if a.strip()] if raw_artist else ["Unknown"]

        source_url = item.get("url", "") or item.get("@id", "")
        seokey = source_url.rstrip("/").split("/")[-1] if source_url else ""

        album = item.get("inAlbum", {}).get("name", "") if isinstance(item.get("inAlbum"), dict) else ""

        songs.append(
            Song(
                title=title,
                artists=artists,
                album=album,
                source="gaana",
                source_id=seokey,
                source_url=source_url,
            )
        )

    logger.info("Gaana: fetched %d songs", len(songs))
    return songs[:limit]
