"""SQLite-backed log of every ping heard, so digiping.zl4st.com can show whether a given request arrived."""

import sqlite3
import time
from pathlib import Path


class PingStore:
    def __init__(self, db_path: str):
        self._path = Path(db_path)
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_call TEXT NOT NULL,
                token TEXT NOT NULL,
                message_text TEXT NOT NULL,
                received_at REAL NOT NULL,
                replied INTEGER NOT NULL DEFAULT 0,
                reply_sent_at REAL
            )
            """
        )
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_pings_from_call ON pings(from_call)")
        self._conn.commit()

    def record_ping(self, from_call: str, token: str, message_text: str) -> int:
        cur = self._conn.execute(
            "INSERT INTO pings (from_call, token, message_text, received_at) VALUES (?, ?, ?, ?)",
            (from_call, token, message_text, time.time()),
        )
        self._conn.commit()
        return cur.lastrowid

    def mark_replied(self, ping_id: int) -> None:
        self._conn.execute(
            "UPDATE pings SET replied = 1, reply_sent_at = ? WHERE id = ?", (time.time(), ping_id),
        )
        self._conn.commit()

    def recent(self, limit: int = 100, from_call: str | None = None) -> list[dict]:
        if from_call:
            rows = self._conn.execute(
                "SELECT * FROM pings WHERE from_call = ? ORDER BY id DESC LIMIT ?",
                (from_call.upper(), limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM pings ORDER BY id DESC LIMIT ?", (limit,),
            ).fetchall()
        columns = [d[0] for d in self._conn.execute("SELECT * FROM pings LIMIT 0").description]
        return [dict(zip(columns, row)) for row in rows]
