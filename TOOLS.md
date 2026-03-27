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
