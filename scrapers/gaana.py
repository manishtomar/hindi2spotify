import json
import logging
import re
from typing import List

import requests
from bs4 import BeautifulSoup

from scrapers import Song

logger = logging.getLogger(__name__)

CHARTS_URL = "https://gaana.com/charts"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
}


def get_songs(limit: int = 30) -> List[Song]:
    """Fetch trending Hindi songs from Gaana's charts page (server-side REDUX_DATA)."""
    try:
        resp = requests.get(CHARTS_URL, headers=HEADERS, timeout=15)
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

    weekly_songs = (
        data.get("chartsReducer", {})
        .get("homepageData", {})
        .get("response", {})
        .get("weekly_data", {})
        .get("songs", [])
    )

    if not weekly_songs:
        logger.warning("Gaana: no songs found in weekly_data")
        return []

    songs: List[Song] = []
    for item in weekly_songs:
        if not isinstance(item, dict):
            continue

        title = item.get("title", "")
        if not title:
            continue

        raw_artists = item.get("subText", "")
        artists = [a.strip() for a in raw_artists.split(",") if a.strip()]
        if not artists:
            artists = ["Unknown"]

        seo = item.get("seo", "")
        source_url = f"https://gaana.com/song/{seo}" if seo else ""

        songs.append(
            Song(
                title=title,
                artists=artists,
                album="",
                source="gaana",
                source_id=str(item.get("id", "")),
                source_url=source_url,
            )
        )

    logger.info("Gaana: fetched %d songs", len(songs))
    return songs[:limit]
