# Video Editing Python Toolkit

A lightweight, fast FFmpeg-based CLI toolkit designed for editing ASMR laptop repair videos and social media content (YouTube long-form, YouTube Shorts, Instagram Reels, TikTok).

## Prerequisites

- Python 3.10+
- FFmpeg and FFprobe installed on your system:
  ```bash
  sudo apt install ffmpeg
  ```

---

## Scripts & Usage

### 1. Cut Video (`cut.py`)
Lossless trimming without re-encoding (instant cuts using FFmpeg stream copy). Supports **single** or **multiple** time periods.

```bash
# Single cut using start & end
python3 cut.py --input raw.mp4 --start 00:01:30 --end 00:05:00

# Single cut using --cuts syntax
python3 cut.py -i raw.mp4 --cuts 00:01:30-00:05:00

# Multiple cuts exported into separate files (e.g. clip_1, clip_2)
python3 cut.py -i raw.mp4 --cuts 00:01:00-00:02:00 00:05:00-00:07:00

# Multiple cuts merged/stitched into ONE continuous video
python3 cut.py -i raw.mp4 --cuts 12-37 57-186 252-517 --merge -o highlight.mp4
```

---

### 2. Fast-Forward / Speed Up (`speedup.py`)
Speed up videos with **pitch-corrected audio** (no chipmunk effect). Supports speeding up the **entire video** (no timestamps required) or **specific segments**.

```bash
# ── Option A: Speed up the entire clip (no timestamps needed) ──
python3 speedup.py --input raw.mp4 --speed 4x
python3 speedup.py -i raw.mp4 --speed 2 -o fast_2x.mp4

# ── Option B: Speed up specific segments (keep rest at 1x) ─────
python3 speedup.py --input raw.mp4 --segments 00:05:00-00:08:00@4x 00:15:00-00:17:00@8x
```

---

### 3. Crop Format (`crop.py`)
Crop landscape 16:9 (1920×1080) video into vertical 9:16 (1080×1920) portrait for Shorts/Reels/TikTok or standardize to landscape.

Supports **custom left & right cropping** with top/bottom filled with a **blurred video background ("shadow")** or **solid black bars**:

```bash
# ── Option A: Left/Right crop with blurred video background (Default) ──
# Crops 200px from left and 150px from right; fills top & bottom with blurred video shadow:
python3 crop.py -i raw.mp4 -f portrait --crop-left 200 --crop-right 150 --fill blur

# ── Option B: Left/Right crop with black bars ────────────────────────
python3 crop.py -i raw.mp4 -f portrait --crop-left 200 --crop-right 150 --fill black

# ── Option C: Keep entire 16:9 width with blurred background ─────────
# Preserves the full width of the laptop/workspace without cutting off sides:
python3 crop.py -i raw.mp4 -f portrait --fill blur

# ── Option D: Full-bleed center crop ─────────────────────────────────
# Crops directly to 9:16 full frame (no padding/bars):
python3 crop.py -i raw.mp4 -f portrait

# Auto-trim to 60 seconds (Shorts limit):
python3 crop.py -i raw.mp4 -f portrait --crop-left 150 --crop-right 150 --max-duration 60
```

---

### 4. Rotate Video (`rotate.py`)
Rotate videos by right angles (90°, 180°, or 270°). Losslessly preserves audio and resets container-level rotation metadata for universal player compatibility.

Supports angles `90`, `180`, `270`, as well as convenient aliases `cw` (clockwise) and `ccw` (counter-clockwise).

```bash
# ── Rotate 90 degrees clockwise ──────────────────────────────────────
python3 rotate.py --input raw.mp4 --angle 90
python3 rotate.py -i raw.mp4 -a cw

# ── Rotate 180 degrees (upside down fix) ─────────────────────────────
python3 rotate.py -i raw.mp4 -a 180

# ── Rotate 90 degrees counter-clockwise (270° clockwise) ─────────────
python3 rotate.py -i raw.mp4 -a ccw
python3 rotate.py -i raw.mp4 -a 270 -o rotated_ccw.mp4
```

---

### 5. Merge Videos (`merge.py`)
Concatenate multiple video files in sequence. Automatically uses lossless stream copy if all clips share exact resolution, codecs, pixel format, and timebase; otherwise re-encodes seamlessly via the concat filter (e.g. when mixing raw camera clips with rotated or edited clips).

```bash
# Merge clips in specified order (auto-detects lossless copy vs re-encode)
python3 merge.py --inputs intro.mp4 main_action.mp4 outro.mp4

# Custom output destination
python3 merge.py -i part1.mp4 part2.mp4 -o full_repair.mp4

# Force re-encoding (e.g. when mixing clips from different sources/encoders)
python3 merge.py -i part1.mp4 part2_rotate_270.mp4 -r -o merged.mp4
```

---

### 6. All-in-One Pipeline (`pipeline.py`)
Chain cut, rotate, speedup, and crop operations into a single command with automatic temporary file cleanup.
Execution order: **Cut → Rotate → Speedup → Crop**.

```bash
# Cut, rotate 90° clockwise, speed up 4x, and crop to portrait:
python3 pipeline.py \
  --input raw.mp4 \
  --cut 00:01:00-00:05:00 \
  --rotate 90 \
  --speedup 4x \
  --crop portrait \
  --crop-left 200 \
  --crop-right 150 \
  --fill blur \
  --output final_short.mp4

# Rotate 90° clockwise and speed up 2x:
python3 pipeline.py -i raw.mp4 --rotate cw --speedup 2x

# Cut multiple sections (auto-stitched), speed up 2x, and crop with black bars:
python3 pipeline.py \
  --input raw.mp4 \
  --cut 12-37 57-186 \
  --speedup 2x \
  --crop portrait \
  --fill black
```

---

## Timestamp Formats Supported

All timestamp fields accept any of these formats:
- `HH:MM:SS` (e.g. `01:02:30`)
- `MM:SS` (e.g. `05:30`)
- Seconds (e.g. `90` or `125.5`)
