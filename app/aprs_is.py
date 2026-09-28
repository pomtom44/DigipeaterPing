"""Persistent APRS-IS connection: logs in as the ping callsign, replies to any PING message addressed to it.

APRS-IS always delivers message-format traffic addressed to your login callsign regardless of any filter,
so no server-side filter is needed here -- just login and read.
"""

import asyncio
import logging
import time

import aprslib

from . import config
from .store import PingStore

logger = logging.getLogger(__name__)

_RECONNECT_DELAY_S = 10
_KEEPALIVE_INTERVAL_S = 180
_DEDUPE_TTL_S = config.DEDUPE_TTL_S


class AprsIsListener:
    def __init__(self, store: PingStore):
        self._store = store
        self._writer: asyncio.StreamWriter | None = None
        # (from_call, token) -> received_at, so a re-heard duplicate (e.g. digipeated twice) isn't re-replied to.
        self._recent_replies: dict[tuple[str, str], float] = {}

    async def run(self) -> None:
        while True:
            try:
                await self._connect_and_listen()
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error("APRS-IS connection failed: %s", e)
            self._writer = None
            await asyncio.sleep(_RECONNECT_DELAY_S)

    async def _connect_and_listen(self) -> None:
        reader, writer = await asyncio.open_connection(config.APRS_IS_SERVER, config.APRS_IS_PORT)
        self._writer = writer
        try:
            login = f"user {config.MYCALL} pass {config.PASSCODE} vers digipeaterping 1.0\r\n"
            writer.write(login.encode())
            await writer.drain()
            logger.info("Logged in to %s:%s as %s", config.APRS_IS_SERVER, config.APRS_IS_PORT, config.MYCALL)

            await asyncio.gather(self._read_loop(reader), self._keepalive_loop())
        finally:
            writer.close()
            self._writer = None

    async def _keepalive_loop(self) -> None:
        while True:
            await asyncio.sleep(_KEEPALIVE_INTERVAL_S)
            if self._writer is not None:
                self._writer.write(b"#keepalive\r\n")
                await self._writer.drain()

    async def _read_loop(self, reader: asyncio.StreamReader) -> None:
        while True:
            line = await reader.readline()
            if not line:
                return  # server closed the connection
            self._handle_line(line.decode(errors="replace").strip())

    def _handle_line(self, line: str) -> None:
        if not line or line.startswith("#"):
            return  # server comment/keepalive line
        try:
            parsed = aprslib.parse(line)
        except Exception:
            return  # not everything on the feed is a decodable APRS packet

        message = parsed.get("subpacket", parsed) if parsed.get("format") == "thirdparty" else parsed
        if message.get("format") != "message":
            return
        addresse = (message.get("addresse") or "").strip().upper()
        if addresse != config.MYCALL.upper():
            return
        from_call = (message.get("from") or "").strip().upper()
        if not from_call or from_call == config.MYCALL.upper():
            return  # ignore our own traffic, avoids reply loops

        text = message.get("message_text", "")
        if not text.upper().startswith("PING"):
            return
        token = text[4:].strip()
        if not token:
            return

        self._prune_recent_replies()
        dedupe_key = (from_call, token)
        if dedupe_key in self._recent_replies:
            return  # already replied to this exact request recently
        self._recent_replies[dedupe_key] = time.time()

        ping_id = self._store.record_ping(from_call, token, text)
        asyncio.create_task(self._reply(from_call, token, ping_id))

    def _prune_recent_replies(self) -> None:
        now = time.time()
        stale = [k for k, t in self._recent_replies.items() if now - t > _DEDUPE_TTL_S]
        for k in stale:
            del self._recent_replies[k]

    async def _reply(self, from_call: str, token: str, ping_id: int) -> None:
        if self._writer is None:
            return
        addressee = from_call.ljust(9)
        line = f"{config.MYCALL}>APRS,TCPIP*::{addressee}:PONG {token}\r\n"
        self._writer.write(line.encode())
        await self._writer.drain()
        self._store.mark_replied(ping_id)
        logger.info("Replied to %s (token %s)", from_call, token)
