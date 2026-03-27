---
name: snap
description: Take a camera snapshot and send it. Usage: /snap
user-invocable: true
---

When the user runs /snap:

1. Stop the stream, take the snapshot, restart the stream:
```bash
pkill -f "ffmpeg.*video0" 2>/dev/null; sleep 2
SNAP=~/cam-snapshots/snapshot-$(date +%Y%m%d-%H%M%S).jpg
fswebcam -r 1280x720 --no-banner -S 20 "$SNAP" 2>/dev/null
python3 ~/.openclaw/workspace/skills/camera/cam_stream.py > /tmp/cam_stream.log 2>&1 &
echo "$SNAP"
```

2. Your entire reply must be ONLY the file path, nothing else. No emoji, no text, just the path:
```
/home/robin/cam-snapshots/snapshot-20260326-130300.jpg
```
