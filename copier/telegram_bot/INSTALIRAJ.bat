@echo off
title SonicCopyX Telegram Bot — Instalacija
color 0A
cd /d "%~dp0"

echo Instaliram pakete...
pip install MetaTrader5 python-telegram-bot requests --quiet

echo.
echo [OK] Gotovo!
echo.
echo Sljedeci korak:
echo   Otvori config.py u Notepadu i popuni:
echo   - MT5 login/password/server
echo   - Telegram TOKEN i CHAT_ID
echo.
echo Kako dobiti Telegram TOKEN i CHAT_ID:
echo   1. Otvori Telegram, trazi @BotFather
echo   2. Pisi /newbot i prati upute
echo   3. Dobit ces TOKEN (dugacki broj:slova)
echo   4. Pisi /start svom botu
echo   5. Otvori u browseru:
echo      https://api.telegram.org/botTOKEN/getUpdates
echo   6. Nadji "chat":{"id": BROJ} - to je CHAT_ID
echo.
pause
