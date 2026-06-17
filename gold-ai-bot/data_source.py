"""Besplatan izvor cene zlata - kad MT5 nije dostupan (npr. signal mode na Macu).

Koristi Yahoo Finance (Gold futures, simbol GC=F) - nema API kljuc, vraca OHLC.
Cene su bliske spot zlatu i sasvim dovoljne za makro signal; tacan broker fid
(npr. XAUUSD.f kod TAG Markets) videces u svom MT5 kad budes unosio nalog.
"""
from __future__ import annotations

import json
import logging
import urllib.request

log = logging.getLogger("data")

_YF_URL = (
    "https://query1.finance.yahoo.com/v8/finance/chart/GC=F"
    "?interval={interval}&range={range}"
)


def fetch_ohlc(interval: str = "15m", days: str = "5d") -> tuple[list[float], list[float], list[float]]:
    """(highs, lows, closes) najstarija -> najnovija. Prazne liste pri gresci."""
    url = _YF_URL.format(interval=interval, range=days)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "gold-ai-bot/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.load(r)
        result = data["chart"]["result"][0]
        q = result["indicators"]["quote"][0]
        highs: list[float] = []
        lows: list[float] = []
        closes: list[float] = []
        for h, l, c in zip(q["high"], q["low"], q["close"]):
            if h is None or l is None or c is None:
                continue
            highs.append(float(h))
            lows.append(float(l))
            closes.append(float(c))
        return highs, lows, closes
    except Exception as e:  # noqa: BLE001
        log.error("Yahoo nije uspeo (%s): %s", url, e)
        return [], [], []


def latest_price() -> float | None:
    _, _, closes = fetch_ohlc(interval="5m", days="1d")
    return closes[-1] if closes else None
