#!/bin/sh
# Start script: logs the PORT env var and starts uvicorn binding to it.
# Reduced workers from 2 -> 1 to lower memory usage and reduce OOM/restart flaps.
# Increased timeout settings for BLIP-2 compatibility (120s → 180s).
if [ -z "$PORT" ]; then
  echo "PORT not set, defaulting to 8000"
  PORT=8000
fi
echo "Starting uvicorn with PORT=${PORT}"
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --workers 1 --timeout-keep-alive 180 --timeout-graceful-shutdown 15
