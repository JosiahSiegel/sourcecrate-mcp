"""Bounded, user-local SQLite cache that never deserializes Python objects."""

import json
import logging
import os
import sqlite3
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class JsonCache:
    def __init__(self, directory: Path, size_limit: int = 1_000_000_000) -> None:
        self.directory = str(directory)
        self.size_limit = size_limit
        self.path = directory / "cache-v1.sqlite3"

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        db = sqlite3.connect(self.path, timeout=5)
        try:
            with db:
                db.execute(
                    "CREATE TABLE IF NOT EXISTS entries (key TEXT PRIMARY KEY, value TEXT NOT NULL, expires REAL, created REAL NOT NULL)"
                )
                yield db
        finally:
            db.close()

    def get(self, key: str, default: Any = None) -> Any:
        try:
            with self._connect() as db:
                row = db.execute(
                    "SELECT value, expires FROM entries WHERE key = ?", (key,)
                ).fetchone()
                if row is None:
                    return default
                if row[1] is not None and row[1] <= time.time():
                    db.execute("DELETE FROM entries WHERE key = ?", (key,))
                    return default
                return json.loads(row[0])
        except (OSError, sqlite3.Error, ValueError, TypeError):
            logger.debug("Ignoring unreadable cache entry", exc_info=True)
            return default

    def set(self, key: str, value: Any, expire: float | None = None) -> bool:
        try:
            serialized = json.dumps(value, ensure_ascii=True, allow_nan=False)
            if len(serialized) > self.size_limit:
                return False
            now = time.time()
            with self._connect() as db:
                # Serialize writers so eviction and insertion respect the shared budget.
                db.execute("BEGIN IMMEDIATE")
                db.execute(
                    "DELETE FROM entries WHERE expires <= ? OR key = ?", (now, key)
                )
                total = db.execute(
                    "SELECT COALESCE(SUM(length(value)), 0) FROM entries"
                ).fetchone()[0]
                for old_key, size in db.execute(
                    "SELECT key, length(value) FROM entries ORDER BY created"
                ).fetchall():
                    if total + len(serialized) <= self.size_limit:
                        break
                    db.execute("DELETE FROM entries WHERE key = ?", (old_key,))
                    total -= size
                db.execute(
                    "INSERT INTO entries VALUES (?, ?, ?, ?)",
                    (key, serialized, None if expire is None else now + expire, now),
                )
            return True
        except (OSError, sqlite3.Error, ValueError, TypeError):
            logger.debug("Skipping unavailable or non-JSON cache write", exc_info=True)
            return False

    def delete(self, key: str) -> bool:
        try:
            with self._connect() as db:
                return (
                    db.execute("DELETE FROM entries WHERE key = ?", (key,)).rowcount > 0
                )
        except (OSError, sqlite3.Error):
            return False

    def volume(self) -> int:
        try:
            return self.path.stat().st_size
        except OSError:
            return 0


# No legacy /tmp pickle cache is opened or migrated. Each user owns their cache.
cache = JsonCache(
    Path(
        os.environ.get(
            "SOURCECRATE_CACHE_DIR", str(Path.home() / ".sourcecrate" / "cache")
        )
    )
)
