"""Signal mode - daj signal sa konkretnim brojevima, ne trguj.

Bot pokupi cenu zlata sa weba (Yahoo) i kontekst, AI analiticar donese odluku,
i ispise GOTOV signal koji rucno unosis u MT5 (mobilni ili desktop):
  smer, entry (oko trenutne cene), SL, TP, predlog lota i rizik u dolarima.

Pokretanje:
    python signal.py

Radi i bez MT5 - savrseno za Mac dok ceka VPS. Treba ti ANTHROPIC_API_KEY u .env.
Za predlog lota dodaj SIGNAL_BALANCE=<tvoj balans> u .env.
"""
from __future__ import annotations

import datetime as _dt
import logging
import os

import config
import data_source
import notify
import risk
from research import ai_analyst, news

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "WARNING"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("signal")


def _suggest_position(price: float, sl_distance: float, balance: float, params, confidence: float):
    """Predlog lota + novcanog rizika/cilja (gold: 1 lot = 100 oz)."""
    if balance <= 0 or sl_distance <= 0:
        return None
    per_lot = 100.0  # $1 cena * 100 oz = $100 po lotu
    targets = risk.money_targets(balance, params, confidence)
    raw_lot = targets.sl_money / (per_lot * sl_distance)
    lot = max(0.01, round(raw_lot / 0.01) * 0.01)
    # stvarni rizik nakon zaokruzivanja lota
    sl_money = per_lot * lot * sl_distance
    tp_distance = targets.tp_money / (per_lot * lot)
    return {
        "lot": lot,
        "sl_money": sl_money,
        "tp_money": targets.tp_money,
        "tp_distance": tp_distance,
    }


def _format_signal(cfg, signal, price, sl_distance, balance: float) -> str:
    now = _dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    bar = "=" * 64
    out = [
        "",
        bar,
        f"  GOLD AI SIGNAL  |  {now}  |  {cfg.symbol} ~{price:.2f}  (izvor: Yahoo GC=F)",
        bar,
        f"  Smer:        {signal.direction.upper()}",
        f"  Sigurnost:   {signal.confidence * 100:.0f}%",
    ]

    if signal.direction in ("buy", "sell"):
        is_buy = signal.direction == "buy"
        sl_price = round(price - sl_distance if is_buy else price + sl_distance, 2)

        pos = _suggest_position(price, sl_distance, balance, cfg.risk, signal.confidence)
        if pos:
            tp_price = round(
                price + pos["tp_distance"] if is_buy else price - pos["tp_distance"], 2
            )
            out += [
                "",
                "  Predlog (rucni unos u MT5):",
                f"    Smer:      {signal.direction.upper()} (market)",
                f"    Entry:     ~{price:.2f}",
                f"    SL:        {sl_price:.2f}   (pomeraj {sl_distance:.2f})",
                f"    TP:        {tp_price:.2f}   (pomeraj {pos['tp_distance']:.2f})",
                f"    Lot:       {pos['lot']:.2f}   (za balans ${balance:.0f})",
                f"    Rizik:     ~{pos['sl_money']:.2f}$   /   Cilj: ~{pos['tp_money']:.2f}$",
            ]
        else:
            out += [
                "",
                "  Predlog (rucni unos u MT5):",
                f"    Smer:      {signal.direction.upper()} (market)",
                f"    Entry:     ~{price:.2f}",
                f"    SL:        {sl_price:.2f}   (pomeraj {sl_distance:.2f})",
                "    (za predlog lota dodaj SIGNAL_BALANCE=<tvoj balans> u .env)",
            ]
    else:
        out += ["", "  HOLD - bez ulaska. Cekaj jasniji signal."]

    out += ["", f"  Razlog:      {signal.reasoning}"]
    if signal.key_factors:
        out += ["  Kljucni faktori:"]
        out += [f"    - {f}" for f in signal.key_factors]
    out += [
        "",
        "  Napomena: cena je sa Yahoo (GC=F); u MT5 koristi TRENUTNU cenu",
        "  brokera i prilagodi entry/SL/TP. Nije finansijski savet.",
        bar,
        "",
    ]
    return "\n".join(out)


def generate() -> None:
    cfg = config.load()
    if not cfg.ai.api_key:
        print("Nedostaje ANTHROPIC_API_KEY u .env - signal mod ga zahteva.")
        return

    highs, lows, closes = data_source.fetch_ohlc(interval="15m", days="5d")
    if not closes:
        print("Ne mogu da povucem cene zlata (Yahoo). Proveri internet i pokusaj ponovo.")
        return

    price = closes[-1]
    technical = risk.technical_summary(closes)
    atr_value = risk.atr(highs, lows, closes, cfg.risk.atr_period)
    sl_distance = atr_value * cfg.risk.atr_sl_mult if atr_value else price * cfg.risk.sl_fallback_pct

    headlines = news.fetch_headlines() if cfg.ai.web_research else []
    signal = ai_analyst.get_signal(
        api_key=cfg.ai.api_key,
        model=cfg.ai.model,
        symbol=cfg.symbol,
        technical=technical,
        web_research=cfg.ai.web_research,
        extra_headlines=headlines,
    )

    balance = float(os.getenv("SIGNAL_BALANCE", "0") or 0)
    text = _format_signal(cfg, signal, price, sl_distance, balance)
    print(text)

    # cuvaj istoriju signala (korisno za pracenje)
    state_dir = os.getenv("STATE_DIR", "logs")
    os.makedirs(state_dir, exist_ok=True)
    with open(os.path.join(state_dir, "signals.log"), "a", encoding="utf-8") as f:
        f.write(text)

    # posalji na Telegram (ako je konfigurisan) - za iPhone/Android obavestenja
    notify.send(text)


if __name__ == "__main__":
    generate()
