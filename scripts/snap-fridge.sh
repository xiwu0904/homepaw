#!/bin/bash
# Take a fridge snapshot. Handles camera lock gracefully.
# Output: the snapshot file path (absolute)

SNAP_DIR="$HOME/cam-snapshots"
mkdir -p "$SNAP_DIR"
SNAP="$SNAP_DIR/fridge-$(date +%Y%m%d-%H%M%S).jpg"

# Release camera if anything is using it
pkill -f "ffmpeg.*video0" 2>/dev/null
pkill -f "cam_stream" 2>/dev/null
sleep 2

# Take snapshot with auto-exposure (skip 20 frames)
fswebcam -r 1280x720 --no-banner -S 20 "$SNAP" 2>/dev/null

# Restart camera stream in background
nohup python3 ~/.openclaw/workspace/skills/camera/cam_stream.py > /tmp/cam_stream.log 2>&1 &

# Output the path
if [ -f "$SNAP" ] && [ -s "$SNAP" ]; then
    echo "$SNAP"
else
    echo "ERROR: snapshot failed" >&2
    exit 1
fi
