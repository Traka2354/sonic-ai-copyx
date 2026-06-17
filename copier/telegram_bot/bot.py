"""
SonicCopyX Telegram Bot — MT5 Tag Markets
Pokretanje: python bot.py

Komande:
  /buy [lots]   - Otvori BUY poziciju
  /sell [lots]  - Otvori SELL poziciju
  /close        - Zatvori sve pozicije
  /status       - Prikazi otvorene pozicije i P&L
  /price        - Trenutna cijena zlata
  /racun        - Stanje accounta
  /kalkulator   - Prikazi profit/gubitak za razlicite lotove
"""

import logging
import asyncio
import sys
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode

import config
import mt5_trader as mt5

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("Bot")


# ── Sigurnost: samo tvoj chat ─────────────────────────────────────────────
def auth(update: Update) -> bool:
    if update.effective_chat.id != config.TELEGRAM_CHAT_ID:
        log.warning(f"Neovlasten pristup od: {update.effective_chat.id}")
        return False
    return True


async def notify(bot: Bot, text: str):
    """Pošalji notifikaciju na tvoj Telegram."""
    try:
        await bot.send_message(
            chat_id=config.TELEGRAM_CHAT_ID,
            text=text,
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        log.error(f"Telegram notify greska: {e}")


# ── /start ────────────────────────────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not auth(update):
        return
    bid, ask = mt5.get_price(config.SYMBOL)
    text = (
        "🤖 <b>SonicCopyX Bot aktivan!</b>\n\n"
        f"📊 Broker: Tag Markets (12X)\n"
        f"💰 Simbol: {config.SYMBOL}\n"
        f"📈 Cijena: <b>{ask:.2f}</b> USD\n"
        f"🎯 TP/SL: ±${config.TP_DOLLARS:.0f} od entry\n\n"
        "<b>Komande:</b>\n"
        "/buy [lots] — Otvori BUY (npr. <code>/buy 0.05</code>)\n"
        "/sell [lots] — Otvori SELL\n"
        "/close — Zatvori sve pozicije\n"
        "/status — Prikazi pozicije i P&amp;L\n"
        "/price — Trenutna cijena\n"
        "/racun — Stanje accounta\n"
        "/kalkulator — Koliko zaradis na $5\n"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


# ── /buy ──────────────────────────────────────────────────────────────────
async def cmd_buy(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not auth(update):
        return

    lots = config.DEFAULT_LOTS
    if ctx.args:
        try:
            lots = float(ctx.args[0])
        except ValueError:
            await update.message.reply_text("❌ Neispravni lot. Primjer: <code>/buy 0.05</code>", parse_mode=ParseMode.HTML)
            return

    await update.message.reply_text(f"⏳ Otvarám BUY {lots} lot {config.SYMBOL}...")

    result = mt5.open_trade(config.SYMBOL, is_buy=True, lots=lots,
                            tp_dollars=config.TP_DOLLARS, sl_dollars=config.SL_DOLLARS)

    if result.success:
        potencijal = round(lots * 100 * config.TP_DOLLARS, 2)
        rizik      = round(lots * 100 * config.SL_DOLLARS, 2)
        text = (
            f"✅ <b>BUY otvoren!</b>\n\n"
            f"🎫 Ticket: #{result.ticket}\n"
            f"📍 Entry: <b>{result.entry:.2f}</b>\n"
            f"🟢 TP: {result.tp:.2f} (+${config.TP_DOLLARS:.0f})\n"
            f"🔴 SL: {result.sl:.2f} (-${config.SL_DOLLARS:.0f})\n"
            f"📦 Lot: {lots}\n\n"
            f"💵 Potencijal: <b>+${potencijal:.2f}</b>\n"
            f"⚠️ Rizik: <b>-${rizik:.2f}</b>"
        )
    else:
        text = f"❌ <b>Greška:</b> {result.message}"

    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


# ── /sell ─────────────────────────────────────────────────────────────────
async def cmd_sell(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not auth(update):
        return

    lots = config.DEFAULT_LOTS
    if ctx.args:
        try:
            lots = float(ctx.args[0])
        except ValueError:
            await update.message.reply_text("❌ Neispravni lot. Primjer: <code>/sell 0.05</code>", parse_mode=ParseMode.HTML)
            return

    await update.message.reply_text(f"⏳ Otvarám SELL {lots} lot {config.SYMBOL}...")

    result = mt5.open_trade(config.SYMBOL, is_buy=False, lots=lots,
                            tp_dollars=config.TP_DOLLARS, sl_dollars=config.SL_DOLLARS)

    if result.success:
        potencijal = round(lots * 100 * config.TP_DOLLARS, 2)
        rizik      = round(lots * 100 * config.SL_DOLLARS, 2)
        text = (
            f"✅ <b>SELL otvoren!</b>\n\n"
            f"🎫 Ticket: #{result.ticket}\n"
            f"📍 Entry: <b>{result.entry:.2f}</b>\n"
            f"🟢 TP: {result.tp:.2f} (-${config.TP_DOLLARS:.0f})\n"
            f"🔴 SL: {result.sl:.2f} (+${config.SL_DOLLARS:.0f})\n"
            f"📦 Lot: {lots}\n\n"
            f"💵 Potencijal: <b>+${potencijal:.2f}</b>\n"
            f"⚠️ Rizik: <b>-${rizik:.2f}</b>"
        )
    else:
        text = f"❌ <b>Greška:</b> {result.message}"

    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


# ── /close ────────────────────────────────────────────────────────────────
async def cmd_close(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not auth(update):
        return

    await update.message.reply_text("⏳ Zatvarám sve pozicije...")

    closed = mt5.close_all(config.SYMBOL)

    if not closed:
        await update.message.reply_text("ℹ️ Nema otvorenih pozicija.")
        return

    total_pnl = sum(t["profit"] for t in closed)
    emoji     = "💚" if total_pnl >= 0 else "🔴"
    lines     = [f"{emoji} <b>Zatvoreno {len(closed)} pozicija</b>\n"]

    for t in closed:
        sign = "+" if t["profit"] >= 0 else ""
        lines.append(f"  #{t['ticket']} → {sign}${t['profit']:.2f}")

    sign_total = "+" if total_pnl >= 0 else ""
    lines.append(f"\n💰 <b>Ukupno: {sign_total}${total_pnl:.2f}</b>")

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


# ── /status ───────────────────────────────────────────────────────────────
async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not auth(update):
        return

    positions = mt5.get_positions(config.SYMBOL)

    if not positions:
        bid, ask = mt5.get_price(config.SYMBOL)
        await update.message.reply_text(
            f"ℹ️ Nema otvorenih pozicija.\n💹 Cijena: {bid:.2f} / {ask:.2f}",
            parse_mode=ParseMode.HTML
        )
        return

    lines = [f"📊 <b>Otvorene pozicije ({config.SYMBOL})</b>\n"]
    total_pnl = 0

    for p in positions:
        emoji = "🟢" if p["pnl_usd"] >= 0 else "🔴"
        sign  = "+" if p["pnl_price"] >= 0 else ""
        lines.append(
            f"{emoji} #{p['ticket']} <b>{p['direction']}</b> {p['lots']} lot\n"
            f"   Entry: {p['entry']:.2f} → Sad: {p['current']:.2f} "
            f"({sign}{p['pnl_price']:.2f})\n"
            f"   P&amp;L: <b>{'+' if p['pnl_usd']>=0 else ''}{p['pnl_usd']:.2f} USD</b>\n"
            f"   TP: {p['tp']:.2f} | SL: {p['sl']:.2f}\n"
        )
        total_pnl += p["pnl_usd"]

    sign_total = "+" if total_pnl >= 0 else ""
    lines.append(f"💰 <b>Ukupni P&amp;L: {sign_total}${total_pnl:.2f}</b>")

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


# ── /price ────────────────────────────────────────────────────────────────
async def cmd_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not auth(update):
        return
    bid, ask = mt5.get_price(config.SYMBOL)
    spread = round(ask - bid, 2)
    await update.message.reply_text(
        f"💹 <b>XAUUSD (Zlato)</b>\n\n"
        f"📉 BID (SELL): <b>{bid:.2f}</b>\n"
        f"📈 ASK (BUY):  <b>{ask:.2f}</b>\n"
        f"↔️ Spread: {spread:.2f}",
        parse_mode=ParseMode.HTML
    )


# ── /racun ────────────────────────────────────────────────────────────────
async def cmd_racun(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not auth(update):
        return
    info = mt5.account_info()
    if not info:
        await update.message.reply_text("❌ Ne mogu dohvatiti podatke o accountu.")
        return
    await update.message.reply_text(
        f"🏦 <b>Tag Markets Account</b>\n\n"
        f"💵 Balance:   <b>{info['balance']:.2f} {info['currency']}</b>\n"
        f"📊 Equity:    <b>{info['equity']:.2f} {info['currency']}</b>\n"
        f"🔒 Margin:    {info['margin']:.2f}\n"
        f"✅ Free:      {info['free']:.2f}\n"
        f"⚡ Leverage:  1:{info['leverage']}",
        parse_mode=ParseMode.HTML
    )


# ── /kalkulator ───────────────────────────────────────────────────────────
async def cmd_kalkulator(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not auth(update):
        return
    bid, _ = mt5.get_price(config.SYMBOL)
    lines = [
        f"🧮 <b>Kalkulator profita — XAUUSD @ {bid:.2f}</b>\n",
        f"Na svakih ${config.TP_DOLLARS:.0f} pomaka cijene:\n",
        f"{'Lot':<8} {'Profit':>8}  {'Gubitak':>10}  {'Margin*':>10}",
        "─" * 42,
    ]
    for lots in [0.01, 0.02, 0.05, 0.10, 0.20, 0.50, 1.00]:
        profit = lots * 100 * config.TP_DOLLARS
        loss   = lots * 100 * config.SL_DOLLARS
        margin = (lots * 100 * bid) / 12  # 12X leverage
        lines.append(f"{lots:<8.2f} +${profit:>6.2f}    -${loss:>6.2f}    ~${margin:>7.2f}")

    lines.append(f"\n* Procjenjeni margin pri 12X leverageu")
    lines.append(f"  Trenutna cijena: {bid:.2f} USD/oz")

    await update.message.reply_text(
        "<pre>" + "\n".join(lines) + "</pre>",
        parse_mode=ParseMode.HTML
    )


# ── Monitor loop — notifikacija kad TP/SL hit ────────────────────────────
async def monitor_positions(bot: Bot):
    """Prati pozicije i šalje notifikaciju kad se zatvore (TP/SL hit)."""
    known_tickets = set()

    while True:
        try:
            positions = mt5.get_positions(config.SYMBOL)
            current_tickets = {p["ticket"] for p in positions}

            # Detektuj zatvorene pozicije
            closed_tickets = known_tickets - current_tickets
            if closed_tickets:
                # Dohvati info iz MT5 historije
                if hasattr(mt5, '_PKG') or True:
                    try:
                        import MetaTrader5 as _mt5
                        from datetime import datetime, timedelta
                        _mt5.history_select(
                            datetime.now() - timedelta(minutes=5),
                            datetime.now()
                        )
                        deals = _mt5.history_deals_get(symbol=config.SYMBOL)
                        if deals:
                            for deal in deals:
                                if deal.position_id in closed_tickets and deal.entry == 1:
                                    profit = round(deal.profit, 2)
                                    emoji  = "💚" if profit >= 0 else "🔴"
                                    reason = "TP ✅" if profit > 0 else ("SL ❌" if profit < 0 else "Zatvoreno")
                                    sign   = "+" if profit >= 0 else ""
                                    await notify(bot,
                                        f"{emoji} <b>Pozicija zatvorena</b>\n"
                                        f"Ticket: #{deal.position_id}\n"
                                        f"Razlog: {reason}\n"
                                        f"P&amp;L: <b>{sign}${profit:.2f}</b>"
                                    )
                    except Exception as e:
                        log.debug(f"Monitor history greska: {e}")

            known_tickets = current_tickets

        except Exception as e:
            log.error(f"Monitor greska: {e}")

        await asyncio.sleep(1)


# ── Main ─────────────────────────────────────────────────────────────────
async def main():
    log.info("Spajam na MT5...")
    if not mt5.connect(config.MT5_LOGIN, config.MT5_PASSWORD, config.MT5_SERVER):
        log.error("MT5 konekcija neuspjesna. Provjeri config.py")
        return

    log.info("Pokrećem Telegram bot...")
    app = Application.builder().token(config.TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start",       cmd_start))
    app.add_handler(CommandHandler("buy",         cmd_buy))
    app.add_handler(CommandHandler("sell",        cmd_sell))
    app.add_handler(CommandHandler("close",       cmd_close))
    app.add_handler(CommandHandler("status",      cmd_status))
    app.add_handler(CommandHandler("price",       cmd_price))
    app.add_handler(CommandHandler("racun",       cmd_racun))
    app.add_handler(CommandHandler("kalkulator",  cmd_kalkulator))

    await notify(app.bot,
        "🚀 <b>SonicCopyX Bot pokrenut!</b>\n"
        f"Broker: Tag Markets | {config.SYMBOL}\n"
        f"TP/SL: ±${config.TP_DOLLARS:.0f}\n"
        "Pisi /start za komande."
    )

    # Pokreni monitor u pozadini
    asyncio.create_task(monitor_positions(app.bot))

    log.info("Bot aktivan. Ctrl+C za zaustavljanje.")
    await app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
