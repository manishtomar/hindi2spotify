import logging
from datetime import datetime, timezone
from typing import List

logger = logging.getLogger(__name__)

BATCH_SIZE = 100


class PlaylistManager:
    def __init__(self, sp, playlist_id: str):
        self.sp = sp
        self.playlist_id = playlist_id

    def update_playlist(self, track_uris: List[str]):
        """Replace all tracks in the playlist with the given URIs."""
        if not track_uris:
            logger.warning("No tracks to update playlist with")
            return

        # Remove duplicates while preserving order
        seen = set()
        unique_uris = []
        for uri in track_uris:
            if uri not in seen:
                seen.add(uri)
                unique_uris.append(uri)
        track_uris = unique_uris

        # First batch: replace (clears existing + adds up to 100)
        first_batch = track_uris[:BATCH_SIZE]
        self.sp.playlist_replace_items(self.playlist_id, first_batch)
        logger.info("Replaced playlist with first %d tracks", len(first_batch))

        # Remaining batches: append
        for i in range(BATCH_SIZE, len(track_uris), BATCH_SIZE):
            batch = track_uris[i : i + BATCH_SIZE]
            self.sp.playlist_add_items(self.playlist_id, batch)
            logger.info("Added batch of %d tracks", len(batch))

        # Update description with timestamp
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        self.sp.playlist_change_details(
            self.playlist_id,
            description=f"Top Hindi songs from JioSaavn & Gaana. Updated {now}.",
        )

        logger.info("Playlist updated with %d tracks", len(track_uris))
