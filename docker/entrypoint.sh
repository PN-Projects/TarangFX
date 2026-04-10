#!/bin/sh
set -e

echo "[entrypoint] Starting local Redis on 127.0.0.1:6379"
redis-server --bind 127.0.0.1 --port 6379 --save "" --appendonly no &

echo "[entrypoint] Starting TarangFX bot"
exec python bot.py
