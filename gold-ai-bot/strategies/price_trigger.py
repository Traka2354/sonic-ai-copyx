"""Deterministicke strategije za pomeraj cene (bez AI).

grid:
  - drzi REFERENTNU cenu (poslednja tacka od koje merimo pomeraj);
  - ako cena PADNE za DELTA od reference -> BUY (kupi jeftino),
  - ako cena PORASTE za DELTA od reference -> SELL (prodaj skupo);
  - posle svakog trejda reference postane trenutna cena.
  Radi odlicno u range trzistu; opasno u jakom trendu (zato je uz zastite:
  max_open_positions, max_total_drawdown, kill-switch).

breakout:
  - prati HIGH i LOW poslednjih N barova (BREAKOUT_LOOKBACK);
  - ako trenutna cena probije high + DELTA -> BUY (jasi trend),
  - ako probije low - DELTA -> SELL.
  Suprotno gridu: dobar u trendu, los u rangeu.

State (referentna cena, ranije okidanja) se pamti u STATE_DIR/strategy_state.json
da bi restart bota nastavio odakle je stao (a ne da svaki put pravi novu referencu).
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass

from config import Config

log = logging.getLogger("strategy")

_STATE_FILE = os.path.join(os.getenv("STATE_DIR", "logs"), "strategy_state.json")


@dataclass
class Signal:
    direction: str          # "buy" | "sell" | "hold"
    reason: str
    reference_price: float | None = None


def _load_state() -> dict:
    try:
        with open(_STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _save_state(state: dict) -> None:
    os.makedirs(os.path.dirname(_STATE_FILE) or ".", exist_ok=True)
    tmp = _STATE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f)
    os.replace(tmp, _STATE_FILE)


def evaluate_grid(price: float, delta: float) -> Signal:
    """BUY kad padne DELTA od reference, SELL kad poraste DELTA. Resetuj ref posle."""
    state = _load_state()
    ref = state.get("grid_ref")
    if ref is None:
        state["grid_ref"] = price
        _save_state(state)
        return Signal(
            "hold",
            f"grid: postavljena referenca {price:.2f}, cekam pomeraj ±{delta:.2f}",
            reference_price=price,
        )

    move = price - float(ref)
    if move >= delta:
        state["grid_ref"] = price
        _save_state(state)
        return Signal(
            "sell",
            f"grid: +{move:.2f} od {ref:.2f} -> SELL (nova ref {price:.2f})",
            reference_price=price,
        )
    if move <= -delta:
        state["grid_ref"] = price
        _save_state(state)
        return Signal(
            "buy",
            f"grid: {move:.2f} od {ref:.2f} -> BUY (nova ref {price:.2f})",
            reference_price=price,
        )
    return Signal(
        "hold",
        f"grid: pomeraj {move:+.2f} od {ref:.2f}, cekam ±{delta:.2f}",
        reference_price=float(ref),
    )


def evaluate_breakout(closes: list[float], delta: float, lookback: int) -> Signal:
    """BUY na probijanje high(N) + DELTA, SELL na probijanje low(N) - DELTA."""
    if len(closes) < lookback + 1:
        return Signal("hold", f"breakout: premalo podataka ({len(closes)} < {lookback + 1})")
    window = closes[-(lookback + 1):-1]  # poslednjih N zatvorenih barova
    price = closes[-1]
    hi = max(window)
    lo = min(window)
    if price > hi + delta:
        return Signal("buy", f"breakout: {price:.2f} > {hi:.2f}+{delta:.2f} -> BUY")
    if price < lo - delta:
        return Signal("sell", f"breakout: {price:.2f} < {lo:.2f}-{delta:.2f} -> SELL")
    return Signal("hold", f"breakout: {price:.2f} u opsegu {lo:.2f}-{hi:.2f}")


def evaluate(cfg: Config, closes: list[float]) -> Signal:
    """Vrati signal prema izabranoj strategiji iz configa."""
    if not closes:
        return Signal("hold", "nema podataka o ceni")
    price = closes[-1]
    kind = cfg.strategy.type
    if kind == "grid":
        return evaluate_grid(price, cfg.strategy.price_trigger_delta)
    if kind == "breakout":
        return evaluate_breakout(closes, cfg.strategy.price_trigger_delta, cfg.strategy.breakout_lookback)
    return Signal("hold", f"nepoznata strategija: {kind}")


def reset() -> None:
    """Obrisi zapamcenu grid referencu - za restart strategije."""
    try:
        os.remove(_STATE_FILE)
    except FileNotFoundError:
        pass
