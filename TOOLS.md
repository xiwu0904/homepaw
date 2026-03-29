# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## HomePaw Setup

### Cameras
- **built-in** → `/dev/video0` (YUYV format, 1280x720 max)
  - Web interface: http://localhost:8088/
  - Skill: `camera` (workspace skill with MJPEG streaming server)
  - Snapshots saved to: `~/cam-snapshots/`
  - Uses `ffmpeg` for streaming, `fswebcam` for standalone snapshots

---

Add whatever helps you do your job. This is your cheat sheet.

### Browser Profiles
- **openclaw** → Managed isolated browser (agent-only, no login state)
  - CDP port: 18800
  - For general web browsing tasks
- **xhs** → Robin's logged-in Chrome session (existing-session driver)
  - User data dir: `~/.config/google-chrome`
  - Already logged into 小红书
  - Use for: recipe search, 小红书 browsing, any site needing login
  - Chrome must be running for this profile to work
  - Robin needs to approve the attach prompt in Chrome

### Browser Notes
- `browser` is a built-in agent tool (like read/write/exec), NOT a bash command
- Never run `browser` via exec/bash — call it directly as a tool
- After config changes, Gateway needs restart for browser to activate

### Image Analysis
- **The agent model (glm-5) cannot analyze images directly.**
- To analyze any image (screenshots, fridge photos, recipe images), use this script:
  ```bash
  python3 ~/.openclaw/workspace/scripts/analyze-image.py --image "/path/to/image.jpg" --prompt "描述你想分析的内容"
  ```
- This script calls Qwen3-VL-Plus API which can actually see and understand images.
- Use it for: analyzing XHS recipe screenshots, identifying fridge contents, reading text from images.
- Do NOT use the built-in `image` tool — it won't work with the current model.
