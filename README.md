# hindi2spotify

Scrapes the top Hindi songs from JioSaavn and Gaana, matches them on Spotify, and keeps two Spotify playlists automatically updated — one per source. Runs daily via GitHub Actions.

## How it works

1. **Scrape** — fetches the top 50 songs from JioSaavn ("Hindi: India Superhits Top 50") and Gaana
2. **Match** — searches Spotify for each song using fuzzy title + artist matching (threshold: 75/100); results are cached in `song_cache.json` to avoid redundant API calls
3. **Sync** — updates two separate Spotify playlists (one for each source) with the matched tracks

## Setup

### 1. Create a Spotify app

- Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) and create an app
- Set the redirect URI to `http://127.0.0.1:8888/callback`
- Note your **Client ID** and **Client Secret**

### 2. Create two Spotify playlists

Create one playlist for JioSaavn songs and one for Gaana songs. Note each playlist's ID (the string in the playlist URL after `/playlist/`).

### 3. Configure environment variables

Copy `.env.example` to `.env` and fill in your values:

```
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
SPOTIFY_REFRESH_TOKEN=your_refresh_token_here
SPOTIFY_SAAVN_PLAYLIST_ID=your_saavn_playlist_id_here
SPOTIFY_GAANA_PLAYLIST_ID=your_gaana_playlist_id_here
```

### 4. Get a refresh token

Run the one-time auth helper to obtain a refresh token:

```bash
uv run setup_auth.py
```

This opens a browser for Spotify authorization and prints the refresh token to add to your `.env`.

## Usage

**Sync playlists** (default — runs both sources):

```bash
uv run main.py
```

**Print songs from a source** without touching Spotify:

```bash
uv run main.py print saavn
uv run main.py print gaana
```

## Automation

A GitHub Actions workflow runs the sync daily at 6:00 AM UTC (11:30 AM IST). To use it:

1. Add the following secrets to your GitHub repository:
   - `SPOTIFY_CLIENT_ID`
   - `SPOTIFY_CLIENT_SECRET`
   - `SPOTIFY_REFRESH_TOKEN`
   - `SPOTIFY_SAAVN_PLAYLIST_ID`
   - `SPOTIFY_GAANA_PLAYLIST_ID`

2. The workflow can also be triggered manually via **Actions → Update Hindi Spotify Playlist → Run workflow**.

The `song_cache.json` file is committed back to the repo after each run to persist the match cache.

## Project structure

```
main.py              # Entry point — auth, scrape, match, sync
matcher.py           # Fuzzy Spotify matching with local cache
normalizer.py        # Title/artist normalization for matching
playlist.py          # Spotify playlist update logic
scrapers/
  jiosaavn.py        # JioSaavn API scraper
  gaana.py           # Gaana scraper
setup_auth.py        # One-time OAuth helper to get a refresh token
song_cache.json      # Cached song→URI mappings (auto-updated)
```
