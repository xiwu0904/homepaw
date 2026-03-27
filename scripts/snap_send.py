#!/usr/bin/env python3
"""Send a camera snapshot directly to a DingTalk user via the API."""
import sys, os, subprocess, requests, json, datetime

CLIENT_ID = "dingv8hxeutmn2oywcse"
CLIENT_SECRET = "O-O4imvRFRSjaonI6riOvifiGrf1XY51Ur9UvYwPHWlk8HzHeFIB9nuPaUhRDhD0"
OAPI = "https://oapi.dingtalk.com"

def get_token():
    r = requests.get(f"{OAPI}/gettoken", params={"appkey": CLIENT_ID, "appsecret": CLIENT_SECRET})
    return r.json()["access_token"]

def take_snapshot():
    snap = os.path.expanduser(f"~/cam-snapshots/snapshot-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.jpg")
    os.makedirs(os.path.dirname(snap), exist_ok=True)
    # Kill the stream server AND ffmpeg so nothing respawns the camera
    subprocess.run("pkill -9 -f 'cam_stream.py' 2>/dev/null; pkill -9 -f 'ffmpeg.*video0' 2>/dev/null", shell=True)
    # Wait until camera is actually free
    import time
    for _ in range(20):
        time.sleep(0.5)
        result = subprocess.run("lsof /dev/video0 2>/dev/null", shell=True, capture_output=True)
        if not result.stdout.strip():
            break
    subprocess.run(f"fswebcam -r 1280x720 --no-banner -S 20 '{snap}' 2>/dev/null", shell=True)
    # Restart stream server in background
    subprocess.Popen(
        f"python3 {os.path.expanduser('~/.openclaw/workspace/skills/camera/cam_stream.py')} > /tmp/cam_stream.log 2>&1",
        shell=True
    )
    return snap

def upload_image(token, path):
    with open(path, "rb") as f:
        r = requests.post(
            f"{OAPI}/media/upload",
            params={"access_token": token, "type": "image"},
            files={"media": (os.path.basename(path), f, "image/jpeg")}
        )
    data = r.json()
    media_id = data.get("media_id", "")
    if media_id.startswith("@"):
        media_id = media_id[1:]
    return media_id

DINGTALK_API = "https://api.dingtalk.com"

def get_v2_token():
    r = requests.post(f"{DINGTALK_API}/v1.0/oauth2/accessToken", json={
        "appKey": CLIENT_ID, "appSecret": CLIENT_SECRET
    })
    return r.json()["accessToken"]

def send_image(token, user_id, media_id):
    r = requests.post(
        f"{DINGTALK_API}/v1.0/robot/oToMessages/batchSend",
        headers={"x-acs-dingtalk-access-token": token, "Content-Type": "application/json"},
        json={
            "robotCode": CLIENT_ID,
            "userIds": [user_id],
            "msgKey": "sampleImageMsg",
            "msgParam": json.dumps({"photoURL": f"@{media_id}"})
        }
    )
    return r.json()

if __name__ == "__main__":
    user_id = sys.argv[1] if len(sys.argv) > 1 else None
    if not user_id:
        print("Usage: snap_send.py <dingtalk_user_id>")
        sys.exit(1)
    print("Taking snapshot...")
    snap = take_snapshot()
    print(f"Saved: {snap}")
    token = get_token()
    v2_token = get_v2_token()
    print("Uploading...")
    media_id = upload_image(token, snap)
    print(f"media_id: {media_id}")
    result = send_image(v2_token, user_id, media_id)
    print(f"Send result: {result}")
