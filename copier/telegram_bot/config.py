# ═══════════════════════════════════════════════════════════════
#   SonicCopyX Telegram Bot — Konfiguracija
# ═══════════════════════════════════════════════════════════════

# ── Telegram ────────────────────────────────────────────────────
# 1. Otvori Telegram → trazi @BotFather
# 2. Pisi /newbot → daj ime → dobit ces TOKEN
# 3. Pisi /start svom botu → idi na:
#    https://api.telegram.org/bot<TOKEN>/getUpdates
#    U "chat":{"id": BROJ} — to je tvoj CHAT_ID
TELEGRAM_TOKEN   = ""      # Npr. "7123456789:AAFxyz..."
TELEGRAM_CHAT_ID = 0       # Npr. 123456789

# ── MT5 Account (Tag Markets) ───────────────────────────────────
MT5_LOGIN    = 0            # Tvoj Tag Markets account broj
MT5_PASSWORD = ""           # Lozinka
MT5_SERVER   = "TagMarkets-Live"  # Provjeri tacno ime u MT5

# ── Strategija ──────────────────────────────────────────────────
SYMBOL        = "XAUUSD"    # Gold
DEFAULT_LOTS  = 0.01        # Defaultni lot ako ne napises (npr /buy → 0.01 lot)
TP_DOLLARS    = 5.0         # Zatvori na +$5 pomaku cijene
SL_DOLLARS    = 5.0         # Zatvori na -$5 pomaku cijene

# ── Napomena: $5 na XAUUSD ──────────────────────────────────────
# 0.01 lot  → $5 pomak = $5  profit/gubitak
# 0.05 lot  → $5 pomak = $25 profit/gubitak
# 0.10 lot  → $5 pomak = $50 profit/gubitak
# 1.00 lot  → $5 pomak = $500 profit/gubitak
# Formula: lots × 100 × $5 = profit u dolarima
