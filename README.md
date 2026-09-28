# DigipeaterPing

A small always-on APRS-IS listener for testing RF reach from an RF-only digipeater to a nearby igate-enabled station.

It logs in to APRS-IS under a callsign you configure. Any APRS message addressed to that callsign starting with `PING <token>` gets an immediate reply: `PONG <token>`, addressed back to the sender. If the requesting station was heard directly on RF by an igate running in full RX & TX mode, that igate will typically relay the reply back out over RF.

Every ping heard is logged (from-callsign, token, timestamp, whether a reply was sent) and shown on a small web dashboard, searchable by callsign, so a station that never gets a reply can still check whether its request was heard at all.

This is the listener side of the [digipeater](https://github.com/pomtom44/digipeater) project's Signal Test feature; see that repo's `OVERVIEW.md` for the full picture of what it's testing and why.

## Running it

```bash
pip install -r requirements.txt
python main.py
```

## Configuration

All via environment variables, no config file:

| Variable | Default | Meaning |
|---|---|---|
| `PING_CALLSIGN` | *(required)* | Base callsign this listener logs in as, no SSID |
| `PING_SSID` | *(none)* | SSID appended to the callsign, e.g. `16` (blank for none) |
| `PING_PASSCODE` | *(computed)* | APRS-IS login passcode; auto-derived from `PING_CALLSIGN` if not set |
| `APRS_IS_SERVER` | `rotate.aprs2.net` | APRS-IS server to connect to |
| `APRS_IS_PORT` | `14580` | APRS-IS port |
| `DB_PATH` | `pings.db` | SQLite file for the ping history |
| `HTTP_PORT` | `8080` | Port for the status dashboard/API |

## Self-hosting

Run this under a callsign you hold, set `PING_CALLSIGN` (and `PING_SSID` if you use one), then point the digipeater's Signal Test tab at that callsign.
