"""Telegram obavestenja - signali i alarmi pravo na telefon (iPhone/Android).

Korisno jer:
  - signal.py salje gotov signal na tvoj Telegram cim ga generise,
  - bot.py salje alarm kad se otvori pozicija ili kad probije DD limit,
  - radi sa bilo kog uredjaja koji ima Telegram - iPhone, Android, desktop.

Setup (jednom):
  1) Otvori Telegram, pretrazi @BotFather, /newbot, prati uputstva -> dobijes TOKEN.
  2) Posalji bilo koju poruku tvom novom botu (mora bar jednom).
  3) U browseru otvori: https://api.telegram.org/bot<TOKEN>/getUpdates
     i pronadji "chat":{"id": ...} -> to je tvoj CHAT_ID.
  4) U .env stavi:
     TELEGRAM_TOKEN=12345:AAA...
     TELEGRAM_CHAT_ID=123456789
  5) Test: python notify.py "Pozdrav sa bota"
"""
from __future__ import annotations

import json
import logging
import os
import sys
import urllib.parse
import urllib.request

log = logging.getLogger("notify")

_API = "https://api.telegram.org/bot{token}/sendMessage"


def send(text: str) -> bool:
    """Posalji tekst na Telegram. Vraca True ako je uspesno (ili False tiho)."""
    token = os.getenv("TELEGRAM_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        return False
    payload = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode("utf-8")
    try:
        req = urllib.request.Request(_API.format(token=token), data=payload)
        with urllib.request.urlopen(req, timeout=10) as r:
            resp = json.load(r)
        if not resp.get("ok"):
            log.warning("Telegram odgovor nije OK: %s", resp)
            return False
        return True
    except Exception as e:  # noqa: BLE001 - obavestenja ne smeju da rusi bota
        log.warning("Telegram greska: %s", e)
        return False


if __name__ == "__main__":
    msg = " ".join(sys.argv[1:]) or "Test poruka iz Gold AI Bota."
    if send(msg):
        print("OK - poruka poslata na Telegram.")
    else:
        print("Nije poslato. Proveri TELEGRAM_TOKEN i TELEGRAM_CHAT_ID u .env.")
