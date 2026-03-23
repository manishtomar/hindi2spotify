import logging
import re
from typing import List

import requests

from scrapers import Song

logger = logging.getLogger(__name__)

API_URL = "https://www.jiosaavn.com/api.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}


def _get_hindi_chart_token() -> str | None:
    """Get the token for a trending Hindi chart playlist."""
    try:
        resp = requests.get(
            API_URL,
            params={"__call": "content.getBrowseModules", "language": "hindi", "_format": "json"},
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error("JioSaavn: failed to fetch chart list: %s", e)
        return None

    charts = data.get("charts", [])
    if not charts:
        return None

    # Prefer a chart with "Trending" in the title
    for chart in charts:
        if "trending" in chart.get("title", "").lower():
            url = chart.get("perma_url", "")
            m = re.search(r"/([^/]+)$", url)
            if m:
                return m.group(1)

    # Fall back to first chart
    url = charts[0].get("perma_url", "")
    m = re.search(r"/([^/]+)$", url)
    return m.group(1) if m else None


def get_songs(limit: int = 30) -> List[Song]:
    """Fetch trending Hindi songs from JioSaavn's Hindi charts."""
    token = _get_hindi_chart_token()
    if not token:
        logger.error("JioSaavn: could not get Hindi chart token")
        return []

    try:
        resp = requests.get(
            API_URL,
            params={
                "__call": "webapi.get",
                "token": token,
                "type": "playlist",
                "_format": "json",
                "n": str(limit),
                "p": "1",
            },
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error("JioSaavn API request failed: %s", e)
        return []

    raw_songs = data.get("songs", [])

    songs: List[Song] = []
    for item in raw_songs:
        if not isinstance(item, dict):
            continue

        title = item.get("song") or item.get("title") or ""
        if not title:
            continue

        raw_artists = (
            item.get("primary_artists")
            or item.get("singers")
            or item.get("music")
            or ""
        )
        artists = [a.strip() for a in raw_artists.split(",") if a.strip()]
        if not artists:
            artists = ["Unknown"]

        album = item.get("album") or item.get("album_name") or ""
        song_id = item.get("id") or item.get("perma_url", "")
        perma_url = item.get("perma_url") or ""

        songs.append(
            Song(
                title=title,
                artists=artists,
                album=album,
                source="jiosaavn",
                source_id=str(song_id),
                source_url=perma_url,
            )
        )

    logger.info("JioSaavn: fetched %d songs", len(songs))
    return songs[:limit]
