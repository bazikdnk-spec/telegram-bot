@echo off
title Telegram Bot - bazikss_bot
cd /d "%~dp0"
echo Запускаю бота...
call venv\Scripts\activate
python main.py
echo.
echo Бот остановлен. Нажмите любую клавишу...
pause
