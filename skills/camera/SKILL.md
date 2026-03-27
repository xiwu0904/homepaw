---
name: camera
description: Control the local webcam — start/stop live stream, take snapshots, and check stream status.
metadata: {"openclaw":{"requires":{"bins":["ffmpeg","python3"]},"os":["linux"]}}
---

# Camera Skill

Control the local webcam at `/dev/video0`. Provides live MJPEG streaming via a web UI and on-demand snapshots.

## Commands

### Start the camera stream
Run the streaming server (if not already running):
```bash
pkill -f "cam_stream.py" 2>/dev/null; sleep 1
python3 {baseDir}/cam_stream.py > /tmp/cam_stream.log 2>&1 &
sleep 3
cat /tmp/cam_stream.log
```
The web UI will be available at **http://localhost:8088/** with Start/Stop/Snapshot buttons.

### Stop the camera stream
```bash
pkill -f "cam_stream.py"; pkill -f "ffmpeg.*video0"
```

### Check stream status
```bash
ps aux | grep cam_stream | grep -v grep && echo "Stream is running" || echo "Stream is stopped"
ss -tlnp | grep 8088
```

### Take a snapshot and send to user on DingTalk
Use this script — it handles stopping the stream, capturing, uploading to DingTalk, and restarting the stream automatically:
```bash
python3 ~/.openclaw/workspace/scripts/snap_send.py <dingtalk_user_id>
```
The user's DingTalk ID is in the conversation metadata as `sender_id`. Example:
```bash
python3 ~/.openclaw/workspace/scripts/snap_send.py 0131111627451036565
```
If successful, the output will contain `processQueryKey` and the image will appear in DingTalk directly.

## Notes
- Camera device: `/dev/video0` (YUYV format, 1280x720)
- Stream port: 8088
- Only one process can use the camera at a time — stop the stream before using `fswebcam` directly
