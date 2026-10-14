"""A content-addressed store for LLM and tool calls (SQLite, thread-safe).

Every entry lives in a *scope*. A scope is a namespace such as "full/base" (one variant's own
runs, used to resume) or "pool/replay" (shared by all variants of a mini, which is what makes
prefix replay and paired runs work). The key is a hash of the call's full input.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
from pathlib import Path
from typing import Any


def key_of(payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(text.encode()).hexdigest()


class Cache:
    def __init__(self, path: Path | str) -> None:
        path = Path(path)
        if str(path) != ":memory:":
            path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(path), check_same_thread=False)
        self._lock = threading.Lock()
        with self._lock:
            self._db.execute("PRAGMA journal_mode=WAL")
            self._db.execute(
                "CREATE TABLE IF NOT EXISTS entries ("
                " scope TEXT NOT NULL, key TEXT NOT NULL, kind TEXT NOT NULL,"
                " value TEXT NOT NULL, PRIMARY KEY (scope, key))"
            )
            self._db.commit()

    def get(self, scope: str, key: str) -> Any | None:
        with self._lock:
            row = self._db.execute(
                "SELECT value FROM entries WHERE scope=? AND key=?", (scope, key)
            ).fetchone()
        return json.loads(row[0]) if row else None

    def put(self, scope: str, key: str, kind: str, value: Any) -> None:
        with self._lock:
            self._db.execute(
                "INSERT OR REPLACE INTO entries VALUES (?,?,?,?)",
                (scope, key, kind, json.dumps(value, ensure_ascii=False)),
            )
            self._db.commit()

    def values(self, scope: str, kind: str) -> list[Any]:
        with self._lock:
            rows = self._db.execute(
                "SELECT value FROM entries WHERE scope=? AND kind=?", (scope, kind)
            ).fetchall()
        return [json.loads(r[0]) for r in rows]
