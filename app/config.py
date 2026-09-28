"""All configuration comes from environment variables; no config file or wizard, this is a single-purpose service."""

import os


def _calculate_passcode(callsign: str) -> int:
    """APRS-IS login passcode, derived from the base callsign (no SSID)."""
    call = callsign.upper().split("-")[0]
    code = 0x73E2
    for i, char in enumerate(call):
        if i % 2 == 0:
            code ^= ord(char) << 8
        else:
            code ^= ord(char)
    return code & 0x7FFF


PING_CALLSIGN = os.environ.get("PING_CALLSIGN", "").strip().upper()
if not PING_CALLSIGN:
    raise RuntimeError("PING_CALLSIGN environment variable is required (your own callsign, no SSID)")
PING_SSID = os.environ.get("PING_SSID", "").strip()
MYCALL = f"{PING_CALLSIGN}-{PING_SSID}" if PING_SSID else PING_CALLSIGN
PASSCODE = int(os.environ.get("PING_PASSCODE", "") or _calculate_passcode(PING_CALLSIGN))

APRS_IS_SERVER = os.environ.get("APRS_IS_SERVER", "rotate.aprs2.net")
APRS_IS_PORT = int(os.environ.get("APRS_IS_PORT", "14580"))

DB_PATH = os.environ.get("DB_PATH", "pings.db")
HTTP_PORT = int(os.environ.get("HTTP_PORT", "8080"))

# Pruned from the reply-dedupe set after this long; matches the digipeater's own signal-test TTL.
DEDUPE_TTL_S = 900
