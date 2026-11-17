"""
Shared FFmpeg utility functions for the video editing toolkit.

Provides helpers for probing video metadata, running FFmpeg commands,
generating output filenames, and parsing timestamps.
"""

import json
import os
import re
import subprocess
import sys


# ── Format presets ──────────────────────────────────────────────────────────

FORMAT_PRESETS = {
    "landscape": {"width": 1920, "height": 1080, "aspect": "16:9"},
    "portrait":  {"width": 1080, "height": 1920, "aspect": "9:16"},
}


# ── Video probing ──────────────────────────────────────────────────────────

def probe_video(path: str) -> dict:
    """
    Probe a video file and return metadata.

    Returns a dict with keys:
        - duration (float): duration in seconds
        - width (int): video width in pixels
        - height (int): video height in pixels
        - fps (float): frames per second
        - video_codec (str): e.g. 'h264'
        - audio_codec (str | None): e.g. 'aac', or None if no audio
        - format (str): container format name
    """
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", "-show_streams",
        path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error probing {path}: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(result.stdout)

    video_stream = next(
        (s for s in data["streams"] if s["codec_type"] == "video"), None
    )
    audio_stream = next(
        (s for s in data["streams"] if s["codec_type"] == "audio"), None
    )

    if video_stream is None:
        print(f"Error: No video stream found in {path}", file=sys.stderr)
        sys.exit(1)

    # Parse FPS from r_frame_rate (e.g. "30/1" or "30000/1001")
    fps_parts = video_stream.get("r_frame_rate", "30/1").split("/")
    fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else 30.0

    # Duration: prefer format duration, fall back to stream duration
    duration = float(
        data.get("format", {}).get("duration")
        or video_stream.get("duration", 0)
    )

    return {
        "duration": duration,
        "width": int(video_stream["width"]),
        "height": int(video_stream["height"]),
        "fps": fps,
        "video_codec": video_stream.get("codec_name", "unknown"),
        "audio_codec": audio_stream.get("codec_name") if audio_stream else None,
        "format": data.get("format", {}).get("format_name", "unknown"),
        "pix_fmt": video_stream.get("pix_fmt"),
        "time_base": video_stream.get("time_base"),
        "sar": video_stream.get("sample_aspect_ratio"),
        "audio_sample_rate": int(audio_stream["sample_rate"]) if audio_stream and "sample_rate" in audio_stream else None,
        "audio_channels": int(audio_stream["channels"]) if audio_stream and "channels" in audio_stream else None,
    }



# ── Running FFmpeg ─────────────────────────────────────────────────────────

def run_ffmpeg(args: list[str], desc: str = "") -> None:
    """
    Run an FFmpeg command. Prints progress to stderr.

    Args:
        args: FFmpeg arguments (without the leading 'ffmpeg').
        desc: Optional description printed before running.
    """
    cmd = ["ffmpeg", "-y", "-hide_banner"] + args
    if desc:
        print(f"⏳ {desc}")
    print(f"   → {' '.join(cmd)}", file=sys.stderr)

    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print(f"❌ FFmpeg failed (exit code {result.returncode})", file=sys.stderr)
        sys.exit(1)

    if desc:
        print(f"✅ {desc} — done")


# ── Timestamp parsing ─────────────────────────────────────────────────────

def parse_timestamp(ts: str) -> float:
    """
    Parse a timestamp string into seconds.

    Accepts:
        - HH:MM:SS      → 01:02:30  = 3750.0
        - HH:MM:SS.mmm  → 00:01:30.500 = 90.5
        - MM:SS          → 05:30     = 330.0
        - Raw seconds    → 90.5      = 90.5
    """
    # Try HH:MM:SS or HH:MM:SS.mmm
    m = re.match(r"^(\d+):(\d+):(\d+)(?:\.(\d+))?$", ts)
    if m:
        h, mn, s = int(m.group(1)), int(m.group(2)), int(m.group(3))
        frac = float(f"0.{m.group(4)}") if m.group(4) else 0.0
        return h * 3600 + mn * 60 + s + frac

    # Try MM:SS
    m = re.match(r"^(\d+):(\d+)(?:\.(\d+))?$", ts)
    if m:
        mn, s = int(m.group(1)), int(m.group(2))
        frac = float(f"0.{m.group(3)}") if m.group(3) else 0.0
        return mn * 60 + s + frac

    # Try raw seconds
    try:
        return float(ts)
    except ValueError:
        print(f"Error: Cannot parse timestamp '{ts}'", file=sys.stderr)
        sys.exit(1)


def format_timestamp(seconds: float) -> str:
    """Format seconds as HH:MM:SS.mmm for FFmpeg."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


# ── Output filename helpers ───────────────────────────────────────────────

def default_output(input_path: str, suffix: str) -> str:
    """
    Generate a default output path by appending a suffix to the input filename.

    Example:
        default_output("/path/to/video.mp4", "portrait") → "/path/to/video_portrait.mp4"
    """
    base, ext = os.path.splitext(input_path)
    # Always output as .mp4
    return f"{base}_{suffix}.mp4"


def ensure_even(n: int) -> int:
    """Ensure a dimension is even (required by most codecs)."""
    return n if n % 2 == 0 else n + 1


# ── atempo filter chain builder ───────────────────────────────────────────

def build_atempo_chain(speed: float) -> str:
    """
    Build a chain of atempo filters for the given speed multiplier.

    FFmpeg's atempo filter only accepts values between 0.5 and 100.0,
    but for best quality, we chain 2.0x filters.

    Examples:
        2.0  → "atempo=2.0"
        4.0  → "atempo=2.0,atempo=2.0"
        8.0  → "atempo=2.0,atempo=2.0,atempo=2.0"
        3.0  → "atempo=2.0,atempo=1.5"
    """
    if speed <= 0:
        raise ValueError("Speed must be positive")

    filters = []
    remaining = speed
    while remaining > 2.0:
        filters.append("atempo=2.0")
        remaining /= 2.0
    if remaining != 1.0:
        filters.append(f"atempo={remaining:.4f}")

    return ",".join(filters) if filters else "atempo=1.0"


# ── Rotation helpers ──────────────────────────────────────────────────────

def parse_rotation_angle(angle: int | str) -> int:
    """
    Parse and validate a rotation angle in right angles (multiples of 90°).

    Accepts:
        - 90, 180, 270 (int or str)
        - 'cw' or '90cw' → 90
        - 'ccw', '90ccw', '-90' → 270
        - '-180', '180cw', '180ccw' → 180
        - '-270', '270ccw' → 90

    Returns:
        Normalized angle: 90, 180, or 270 (degrees clockwise).

    Raises:
        ValueError: If the angle is not a supported right angle (90, 180, 270).
    """
    if isinstance(angle, (int, float)):
        val = int(angle)
        norm = val % 360
        if norm in (90, 180, 270):
            return norm
        raise ValueError(f"Invalid rotation angle: {angle}°. Only right angles (90, 180, 270) are supported.")

    s = str(angle).strip().lower()
    if s in ("cw", "+cw"):
        return 90
    if s in ("ccw", "+ccw"):
        return 270

    # Remove optional unit suffix (e.g. "deg", "degrees")
    s = re.sub(r"\s*(degrees?|deg)$", "", s)

    # Check for direction suffixes like "90cw" or "90ccw"
    is_ccw = False
    if s.endswith("ccw"):
        is_ccw = True
        s = s[:-3].strip()
    elif s.endswith("cw"):
        s = s[:-2].strip()

    try:
        val = int(s)
    except ValueError:
        raise ValueError(
            f"Cannot parse rotation angle '{angle}'. Expected 90, 180, 270, cw, or ccw."
        )

    if is_ccw:
        val = -val

    norm = val % 360
    if norm in (90, 180, 270):
        return norm

    raise ValueError(
        f"Invalid rotation angle: {angle}. Only right angles (90°, 180°, 270°) are supported."
    )


def get_rotation_filter(angle: int) -> str:
    """
    Return the FFmpeg video filter for a right-angle rotation (in clockwise degrees).

    - 90°  → 'transpose=1' (90 degrees clockwise)
    - 180° → 'hflip,vflip' (180 degrees)
    - 270° → 'transpose=2' (90 degrees counter-clockwise / 270 degrees clockwise)
    """
    if angle == 90:
        return "transpose=1"
    elif angle == 180:
        return "hflip,vflip"
    elif angle == 270:
        return "transpose=2"
    else:
        raise ValueError(
            f"Unsupported rotation angle: {angle}. Only 90, 180, and 270 degrees are supported."
        )

