#!/usr/bin/env bash
set -euo pipefail
echo "Starting run_bot.sh at $(date -u)" | tee bot_debug.log

echo "---- Print current directory ----" | tee -a bot_debug.log
pwd | tee -a bot_debug.log
ls -la | tee -a bot_debug.log

echo "---- Print python info ----" | tee -a bot_debug.log
python -V 2>&1 | tee -a bot_debug.log
pip -V 2>&1 | tee -a bot_debug.log

echo "---- Show (masked) env availability ----" | tee -a bot_debug.log
if [ -z "${TELEGRAM_BOT_TOKEN:-}" ]; then echo "TELEGRAM_BOT_TOKEN: MISSING" | tee -a bot_debug.log; else echo "TELEGRAM_BOT_TOKEN: PRESENT" | tee -a bot_debug.log; fi
if [ -z "${CHAT_ID:-}" ]; then echo "CHAT_ID: MISSING" | tee -a bot_debug.log; else echo "CHAT_ID: PRESENT" | tee -a bot_debug.log; fi
if [ -z "${GEMINI_API_KEY:-}" ]; then echo "GEMINI_API_KEY: MISSING" | tee -a bot_debug.log; else echo "GEMINI_API_KEY: PRESENT" | tee -a bot_debug.log; fi

echo "---- Running main.py ----" | tee -a bot_debug.log
# Run Python with unbuffered stdout so logs stream in Actions
python -u main.py 2>&1 | tee -a bot_debug.log || ( echo "main.py exit code $?"; exit 1 )
echo "Completed run_bot.sh at $(date -u)" | tee -a bot_debug.log


