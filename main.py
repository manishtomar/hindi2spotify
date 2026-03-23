import logging
import os
import sys

import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

from matcher import SpotifyMatcher
from playlist import PlaylistManager
from scrapers.gaana import get_songs as get_gaana_songs
from scrapers.jiosaavn import get_songs as get_jiosaavn_songs

# Logging: stdout + file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("hindi2spotify.log", mode="w"),
    ],
)
logger = logging.getLogger(__name__)


def get_spotify_client() -> spotipy.Spotify:
    """Authenticate with Spotify using a refresh token."""
    client_id = os.environ["SPOTIFY_CLIENT_ID"]
    client_secret = os.environ["SPOTIFY_CLIENT_SECRET"]
    refresh_token = os.environ["SPOTIFY_REFRESH_TOKEN"]

    oauth = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri="http://127.0.0.1:8888/callback",
        scope="playlist-modify-public playlist-modify-private",
    )
    token_info = oauth.refresh_access_token(refresh_token)
    return spotipy.Spotify(auth=token_info["access_token"])


def main():
    load_dotenv()

    logger.info("Starting hindi2spotify")

    # Authenticate
    try:
        sp = get_spotify_client()
        logger.info("Spotify authentication successful")
    except Exception as e:
        logger.error("Spotify authentication failed: %s", e)
        sys.exit(1)

    playlist_id = os.environ.get("SPOTIFY_PLAYLIST_ID")
    if not playlist_id:
        logger.error("SPOTIFY_PLAYLIST_ID not set")
        sys.exit(1)

    # Scrape songs from both sources independently
    all_songs = []

    try:
        jiosaavn_songs = get_jiosaavn_songs(30)
        all_songs.extend(jiosaavn_songs)
        logger.info("JioSaavn: got %d songs", len(jiosaavn_songs))
    except Exception as e:
        logger.error("JioSaavn scraper failed: %s", e)

    try:
        gaana_songs = get_gaana_songs(30)
        all_songs.extend(gaana_songs)
        logger.info("Gaana: got %d songs", len(gaana_songs))
    except Exception as e:
        logger.error("Gaana scraper failed: %s", e)

    if not all_songs:
        logger.error("No songs scraped from any source")
        sys.exit(1)

    # Deduplicate
    unique_songs = list(set(all_songs))
    logger.info("Total unique songs: %d (from %d raw)", len(unique_songs), len(all_songs))

    # Match on Spotify
    matcher = SpotifyMatcher(sp)
    track_uris = matcher.match_songs(unique_songs)

    if not track_uris:
        logger.error("No songs matched on Spotify")
        sys.exit(1)

    # Update playlist
    playlist_mgr = PlaylistManager(sp, playlist_id)
    playlist_mgr.update_playlist(track_uris)

    logger.info("Done! Playlist updated with %d tracks", len(track_uris))


if __name__ == "__main__":
    main()
