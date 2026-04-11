import argparse
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


def cmd_print(source: str) -> None:
    """Print songs from the given source without touching Spotify."""
    if source == "saavn":
        songs = get_jiosaavn_songs(50)
    else:
        songs = get_gaana_songs(50)

    for i, song in enumerate(songs, 1):
        artists = ", ".join(song.artists)
        print(f"{i:2}. {song.title} — {artists}")


def main():
    parser = argparse.ArgumentParser(prog="hindi2spotify")
    subparsers = parser.add_subparsers(dest="command")

    print_parser = subparsers.add_parser("print", help="Print songs from a source")
    print_parser.add_argument(
        "source", choices=["saavn", "gaana"], help="Source to fetch songs from"
    )

    args = parser.parse_args()

    if args.command == "print":
        load_dotenv()
        cmd_print(args.source)
        return

    # Default: sync to Spotify
    load_dotenv()

    logger.info("Starting hindi2spotify")

    # Authenticate
    try:
        sp = get_spotify_client()
        logger.info("Spotify authentication successful")
    except Exception as e:
        logger.error("Spotify authentication failed: %s", e)
        sys.exit(1)

    saavn_playlist_id = os.environ.get("SPOTIFY_SAAVN_PLAYLIST_ID")
    gaana_playlist_id = os.environ.get("SPOTIFY_GAANA_PLAYLIST_ID")
    if not saavn_playlist_id or not gaana_playlist_id:
        logger.error("SPOTIFY_SAAVN_PLAYLIST_ID and SPOTIFY_GAANA_PLAYLIST_ID must both be set")
        sys.exit(1)

    matcher = SpotifyMatcher(sp)

    sources = [
        ("JioSaavn", get_jiosaavn_songs, saavn_playlist_id),
        ("Gaana", get_gaana_songs, gaana_playlist_id),
    ]

    for source_name, get_songs, playlist_id in sources:
        logger.info("Processing %s", source_name)
        try:
            songs = get_songs(50)
            logger.info("%s: got %d songs", source_name, len(songs))
        except Exception as e:
            logger.error("%s scraper failed: %s", source_name, e)
            continue

        if not songs:
            logger.warning("%s: no songs scraped, skipping", source_name)
            continue

        track_uris = matcher.match_songs(songs)
        if not track_uris:
            logger.warning("%s: no songs matched on Spotify, skipping", source_name)
            continue

        playlist_mgr = PlaylistManager(sp, playlist_id, source_name)
        playlist_mgr.update_playlist(track_uris)
        logger.info("%s: playlist updated with %d tracks", source_name, len(track_uris))

    logger.info("Done!")


if __name__ == "__main__":
    main()
