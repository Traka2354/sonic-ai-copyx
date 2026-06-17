@echo off
title SonicCopyX Telegram Bot — AKTIVAN
color 0A
cd /d "%~dp0"

:start
echo ============================================
echo   SonicCopyX Telegram Bot
echo   Zaustavi: Ctrl+C ili zatvori prozor
echo ============================================
echo.
python bot.py
echo.
echo [!] Bot se ugasio. Restartuje za 5s...
timeout /t 5 /nobreak >nul
goto start
