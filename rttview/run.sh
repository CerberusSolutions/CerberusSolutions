#!/usr/bin/env bash
# macOS/Linux launcher for rttview.  Usage: ./run.sh [folder-of-RTT-files]
cd "$(dirname "$0")"
exec python3 -m rttview "${1:-samples}"
