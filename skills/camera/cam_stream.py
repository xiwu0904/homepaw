#!/usr/bin/env python3
"""MJPEG streaming server with web UI"""
import http.server, socketserver, subprocess, threading, sys, time

PORT = 8088
frame_lock = threading.Lock()
current_frame = b""
frame_id = 0

HTML = b"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Camera</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{background:#1a1a2e;color:#eee;font-family:system-ui;display:flex;flex-direction:column;align-items:center;min-height:100vh;padding:20px}h1{margin-bottom:16px;font-size:1.4em}#feed{max-width:100%;border-radius:8px;background:#000}.controls{margin-top:16px;display:flex;gap:12px}button{padding:10px 24px;border:none;border-radius:6px;font-size:1em;cursor:pointer;font-weight:600}#startBtn{background:#00c853;color:#fff}#stopBtn{background:#ff1744;color:#fff}#snapBtn{background:#2979ff;color:#fff}button:hover{opacity:0.85}#status{margin-top:12px;font-size:0.9em;color:#aaa}</style></head><body>
<h1>&#128247; Live Camera</h1>
<img id="feed" width="1280" height="720"/>
<div class="controls">
<button id="startBtn" onclick="startStream()">&#9654; Start</button>
<button id="stopBtn" onclick="stopStream()">&#9632; Stop</button>
<button id="snapBtn" onclick="takeSnap()">&#128248; Snapshot</button>
</div><div id="status">Connecting...</div>
<script>
const f=document.getElementById('feed'),s=document.getElementById('status');
function startStream(){f.src='/stream?'+Date.now();s.textContent='Streaming...'}
function stopStream(){f.src='';s.textContent='Stopped'}
function takeSnap(){window.open('/snap?'+Date.now(),'_blank')}
f.onload=()=>s.textContent='Streaming...';
f.onerror=()=>s.textContent='Connection lost. Click Start.';
startStream();
</script></body></html>"""

def capture_loop():
    global current_frame, frame_id
    while True:
        try:
            proc = subprocess.Popen(
                ['ffmpeg','-f','v4l2','-input_format','yuyv422',
                 '-video_size','1280x720','-framerate','10',
                 '-i','/dev/video0','-c:v','mjpeg','-q:v','5',
                 '-f','image2pipe','-vcodec','mjpeg','-'],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            buf = b""
            while True:
                chunk = proc.stdout.read(8192)
                if not chunk: break
                buf += chunk
                while True:
                    s = buf.find(b'\xff\xd8')
                    e = buf.find(b'\xff\xd9', s+2) if s != -1 else -1
                    if s == -1 or e == -1:
                        if len(buf) > 500000: buf = buf[-100000:]
                        break
                    with frame_lock:
                        current_frame = buf[s:e+2]
                        frame_id += 1
                    buf = buf[e+2:]
        except Exception:
            pass
        time.sleep(2)

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200); self.send_header('Content-Type','text/html'); self.end_headers()
            self.wfile.write(HTML)
        elif self.path.startswith('/stream'):
            self.send_response(200)
            self.send_header('Content-Type','multipart/x-mixed-replace; boundary=frame')
            self.send_header('Cache-Control','no-cache, no-store')
            self.end_headers()
            try:
                lid = -1
                while True:
                    with frame_lock: fid, f = frame_id, current_frame
                    if fid > lid and f:
                        self.wfile.write(b'--frame\r\nContent-Type: image/jpeg\r\nContent-Length: %d\r\n\r\n' % len(f))
                        self.wfile.write(f); self.wfile.write(b'\r\n'); self.wfile.flush()
                        lid = fid
                    else: time.sleep(0.03)
            except (BrokenPipeError, ConnectionResetError, OSError): pass
        elif self.path.startswith('/snap'):
            with frame_lock: f = current_frame
            if f:
                import os, datetime
                snap_dir = os.path.expanduser('~/cam-snapshots')
                os.makedirs(snap_dir, exist_ok=True)
                fname = datetime.datetime.now().strftime('snapshot-%Y%m%d-%H%M%S.jpg')
                fpath = os.path.join(snap_dir, fname)
                with open(fpath, 'wb') as fp: fp.write(f)
                self.send_response(200); self.send_header('Content-Type','image/jpeg')
                self.send_header('Content-Disposition', f'attachment; filename="{fname}"')
                self.send_header('Content-Length',str(len(f))); self.end_headers()
                self.wfile.write(f)
            else: self.send_error(503,'No frame yet')
        else: self.send_error(404)
    def log_message(self, *a): pass

class S(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

if __name__ == '__main__':
    srv = S(("0.0.0.0", PORT), Handler)
    print(f"http://localhost:{PORT}/", flush=True)
    threading.Thread(target=capture_loop, daemon=True).start()
    srv.serve_forever()
