"""
One-time OAuth setup helper.

Run locally to obtain a Spotify refresh token:
    python setup_auth.py

Prerequisites:
    1. Create a Spotify app at https://developer.spotify.com/dashboard
    2. Set redirect URI to http://127.0.0.1:8888/callback
    3. Copy Client ID and Client Secret into .env
"""

import os
import sys

from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth


def main():
    load_dotenv()

    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("Error: Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in .env")
        sys.exit(1)

    oauth = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri="http://127.0.0.1:8888/callback",
        scope="playlist-modify-public playlist-modify-private",
        open_browser=True,
    )

    print("Opening browser for Spotify authorization...")
    print("After authorizing, you'll be redirected to localhost.")
    print()

    token_info = oauth.get_access_token(as_dict=True)

    if not token_info or "refresh_token" not in token_info:
        print("Error: Could not obtain refresh token")
        sys.exit(1)

    refresh_token = token_info["refresh_token"]

    print("=" * 60)
    print("SUCCESS! Your refresh token:")
    print()
    print(f"  {refresh_token}")
    print()
    print("Store this as a GitHub Actions secret:")
    print("  Secret name: SPOTIFY_REFRESH_TOKEN")
    print("  Secret value: <the token above>")
    print()
    print("Also add to .env for local testing:")
    print(f"  SPOTIFY_REFRESH_TOKEN={refresh_token}")
    print("=" * 60)


if __name__ == "__main__":
    main()
