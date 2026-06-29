---
name: import
description: Import files (photos, video) from the user's phone connected via USB. Use when the user says "pull files from my phone", "copy photos/video from phone", "import from phone", "get the video off my phone", or asks you to access files on a connected Pixel/Android device.
version: 1.0.0
---

# Skill: Phone Import

Copy files from a Pixel phone connected via USB (MTP) and optionally extract
video frames for processing.

## Prerequisites

- Phone connected via USB, **unlocked**, and set to **File Transfer** mode
  (pull down notification shade on the phone to change USB mode)
- For frame extraction: `ffmpeg` must be on PATH
  (`winget install ffmpeg` or `scoop install ffmpeg`)

## Entry Point

```
uv run D:/_code/home/tools/phone_import.py <command> [options]
```

Run from the target repo directory (usually `D:/_code/home`).

---

## Commands

### List files on the phone

```
uv run D:/_code/home/tools/phone_import.py list [--type photo|video|all] [--after YYYY-MM-DD] [--before YYYY-MM-DD] [--latest N] [--json]
```

- `--type`: Filter by file type (default: all)
- `--after` / `--before`: Filter by date (parsed from PXL_YYYYMMDD filenames)
- `--latest N`: Show only the N most recent files
- `--json`: Output as JSON array (for programmatic use)

### Copy files to local disk

```
uv run D:/_code/home/tools/phone_import.py copy [FILE ...] [--type photo|video|all] [--after YYYY-MM-DD] [--latest N] [--dest DIR]
```

- Pass explicit filenames OR use `--type`/`--after`/`--latest` filters
- `--dest`: Destination directory (default: `output/phone/`)
- Outputs JSON summary to stdout with dest path and file list

### Extract frames from video

```
uv run D:/_code/home/tools/phone_import.py frames <video-path> [--fps FPS] [--dest DIR]
```

- `--fps`: Frames per second to extract (default: 1.0). Use 0.5 for one frame
  every 2 seconds, 2.0 for two frames per second.
- `--dest`: Output directory (default: `<video-name>_frames/`)
- Requires ffmpeg on PATH
- Outputs JSON summary with frame count and dest path

---

## Typical Workflow

### 1. Check the phone is visible

```
uv run D:/_code/home/tools/phone_import.py list --type video --latest 5
```

If this fails, tell the user to:
1. Unlock the phone
2. Pull down the notification shade
3. Tap the USB notification and select "File Transfer"

### 2. Copy today's video

```
uv run D:/_code/home/tools/phone_import.py copy --type video --after 2026-06-29 --dest output/phone
```

### 3. Extract frames for 3D pipeline

```
uv run D:/_code/home/tools/phone_import.py frames output/phone/PXL_20260629_XXXXXX.mp4 --fps 1 --dest output/frames
```

For the 3D model pipeline, 1 fps is a good starting point. Increase to 2 fps
for fast-moving video or decrease to 0.5 fps for slow walks.

### 4. Process frames

The extracted JPEG frames in the output directory are ready for the object
detection and constraint pipeline in `home/tools/scene_models.py`.

---

## Device Configuration

The script defaults to:
- Device: "Pixel 10"
- Storage: "Internal shared storage"
- Camera folder: "DCIM/Camera"

These are hardcoded for Chip's Pixel 10. If the device changes, update the
constants at the top of `phone_import.py`.
