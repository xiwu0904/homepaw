#!/bin/bash
# Camera Stream Startup Script
pkill -f "cam_stream.py" 2>/dev/null; sleep 1
python3 ~/.openclaw/workspace/skills/camera/cam_stream.py > /tmp/cam_stream.log 2>&1 &
sleep 3
cat /tmp/cam_stream.log
