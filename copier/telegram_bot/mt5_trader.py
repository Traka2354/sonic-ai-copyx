"""MT5 trade execution i monitoring za Tag Markets."""

import logging
import time
from dataclasses import dataclass
from typing import Optional

log = logging.getLogger("MT5")

try:
    import MetaTrader5 as mt5
    _PKG = True
except ImportError:
    _PKG = False


@dataclass
class TradeResult:
    success: bool
    ticket:  int    = 0
    message: str    = ""
    entry:   float  = 0.0
    tp:      float  = 0.0
    sl:      float  = 0.0
    lots:    float  = 0.0


def connect(login: int, password: str, server: str) -> bool:
    if not _PKG:
        log.error("MetaTrader5 paket nije instaliran")
        return False
    if not mt5.initialize():
        log.error(f"MT5 initialize greska: {mt5.last_error()}")
        return False
    if login:
        if not mt5.login(login, password=password, server=server):
            log.error(f"MT5 login greska: {mt5.last_error()}")
            return False
    info = mt5.account_info()
    if not info:
        return False
    log.info(f"MT5 spojen: #{info.login} | {info.company} | Balance: {info.balance:.2f}")
    return True


def disconnect():
    if _PKG:
        mt5.shutdown()


def get_price(symbol: str) -> tuple[float, float]:
    """Vrati (bid, ask) trenutnu cijenu."""
    if not _PKG:
        return 0.0, 0.0
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return 0.0, 0.0
    return tick.bid, tick.ask


def account_info() -> dict:
    if not _PKG:
        return {}
    info = mt5.account_info()
    if not info:
        return {}
    return {
        "balance":  info.balance,
        "equity":   info.equity,
        "margin":   info.margin,
        "free":     info.margin_free,
        "currency": info.currency,
        "leverage": info.leverage,
    }


def open_trade(symbol: str, is_buy: bool, lots: float,
               tp_dollars: float, sl_dollars: float) -> TradeResult:
    """Otvori trejd sa TP i SL u dolarima pomaka od entry cijene."""
    if not _PKG:
        return TradeResult(False, message="MetaTrader5 nije dostupan")

    bid, ask = get_price(symbol)
    if bid == 0:
        return TradeResult(False, message=f"Ne mogu dohvatiti cijenu za {symbol}")

    if is_buy:
        entry = ask
        tp    = round(entry + tp_dollars, 2)
        sl    = round(entry - sl_dollars, 2)
        order_type = mt5.ORDER_TYPE_BUY
        price = ask
    else:
        entry = bid
        tp    = round(entry - tp_dollars, 2)
        sl    = round(entry + sl_dollars, 2)
        order_type = mt5.ORDER_TYPE_SELL
        price = bid

    request = {
        "action":       mt5.TRADE_ACTION_DEAL,
        "symbol":       symbol,
        "volume":       lots,
        "type":         order_type,
        "price":        price,
        "sl":           sl,
        "tp":           tp,
        "deviation":    30,
        "magic":        99999,
        "comment":      "SonicBot",
        "type_time":    mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)

    if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
        code = result.retcode if result else "?"
        msg  = result.comment if result else str(mt5.last_error())
        return TradeResult(False, message=f"Greska {code}: {msg}")

    direction = "BUY" if is_buy else "SELL"
    log.info(f"Otvoren trejd: #{result.order} {direction} {lots} {symbol} @ {entry:.2f} | TP:{tp:.2f} SL:{sl:.2f}")

    return TradeResult(
        success=True,
        ticket=result.order,
        entry=entry,
        tp=tp,
        sl=sl,
        lots=lots,
        message="OK",
    )


def close_all(symbol: str) -> list[dict]:
    """Zatvori sve otvorene pozicije za symbol. Vraca listu zatvorenih."""
    if not _PKG:
        return []

    positions = mt5.positions_get(symbol=symbol)
    if not positions:
        return []

    closed = []
    for pos in positions:
        bid, ask = get_price(symbol)
        if pos.type == mt5.ORDER_TYPE_BUY:
            close_price = bid
            close_type  = mt5.ORDER_TYPE_SELL
        else:
            close_price = ask
            close_type  = mt5.ORDER_TYPE_BUY

        req = {
            "action":       mt5.TRADE_ACTION_DEAL,
            "symbol":       symbol,
            "volume":       pos.volume,
            "type":         close_type,
            "position":     pos.ticket,
            "price":        close_price,
            "deviation":    30,
            "magic":        99999,
            "comment":      "SonicBot-Close",
            "type_time":    mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(req)
        profit = round(pos.profit, 2)

        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            log.info(f"Zatvoren #{pos.ticket} | P&L: {profit:+.2f}")
            closed.append({"ticket": pos.ticket, "profit": profit, "lots": pos.volume})
        else:
            code = result.retcode if result else "?"
            log.error(f"Greska zatvaranja #{pos.ticket}: {code}")

    return closed


def get_positions(symbol: str) -> list[dict]:
    """Vrati sve otvorene pozicije sa trenutnim P&L."""
    if not _PKG:
        return []
    positions = mt5.positions_get(symbol=symbol)
    if not positions:
        return []

    bid, ask = get_price(symbol)
    result = []
    for p in positions:
        direction = "BUY" if p.type == 0 else "SELL"
        current   = bid if p.type == 0 else ask
        pnl_price = round(current - p.price_open, 2) if p.type == 0 else round(p.price_open - current, 2)
        result.append({
            "ticket":    p.ticket,
            "direction": direction,
            "lots":      p.volume,
            "entry":     p.price_open,
            "current":   current,
            "pnl_price": pnl_price,
            "pnl_usd":   round(p.profit, 2),
            "tp":        p.tp,
            "sl":        p.sl,
        })
    return result
