#!/bin/sh
set -e
./app/scripts/download_data.sh
exec uvicorn app.main:app --host 0.0.0.0 --port 8000