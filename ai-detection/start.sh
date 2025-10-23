#!/bin/sh
# Start script: logs the PORT env var and starts uvicorn binding to it.
if [ -z "$PORT" ]; then
  echo "PORT not set, defaulting to 8000"
  PORT=8000
fi
echo "Starting uvicorn with PORT=${PORT}"
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --workers 2
