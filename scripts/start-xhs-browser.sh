#!/bin/bash
# Start Chrome with XHS profile for OpenClaw browser automation
# This Chrome instance has Robin's XHS login cookies and listens on CDP port 9222

# Kill any existing instance on port 9222
pkill -f "remote-debugging-port=9222" 2>/dev/null
sleep 1

/opt/google/chrome/chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/home/robin/.openclaw/browser/xhs/user-data \
  --no-sandbox \
  --no-first-run \
  --disable-gpu \
  &

echo "XHS Chrome started on CDP port 9222"
echo "Verify: curl -s http://127.0.0.1:9222/json/version"
