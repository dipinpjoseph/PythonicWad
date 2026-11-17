#!/usr/bin/env python3
"""
Rotate a video by right angles (90°, 180°, or 270°).

Supports:
- 90° clockwise (90, cw, 90cw)
- 180° (180, 180cw, 180ccw)
- 270° clockwise / 90° counter-clockwise (270, ccw, 90ccw)

Losslessly copies the audio stream when present. Resets any container-level
rotation metadata so that output video is physically rotated and displays
consistently across all media players.

Usage examples:
    # Rotate 90 degrees clockwise:
    python rotate.py --input video.mp4 --angle 90
    python rotate.py -i video.mp4 -a cw

    # Rotate 180 degrees (upside down fix):
    python rotate.py -i video.mp4 -a 180

    # Rotate 90 degrees counter-clockwise (270° clockwise):
    python rotate.py -i video.mp4 -a ccw
    python rotate.py -i video.mp4 -a 270 -o rotated_ccw.mp4
"""

import argparse
import os
import sys

from ffmpeg_utils import (
    default_output,
    get_rotation_filter,
    parse_rotation_angle,
    probe_video,
    run_ffmpeg,
)


def rotate_video(
    input_path: str,
    angle: int | str,
    output_path: str | None = None,
) -> str:
    """
    Rotate a video by right angles (90°, 180°, or 270° clockwise).

    Args:
        input_path: Path to the input video file.
        angle: Rotation angle (90, 180, 270, or 'cw', 'ccw', etc.).
        output_path: Output file path. Defaults to auto-generated path if None.

    Returns:
        The output file path.
    """
    if not os.path.isfile(input_path):
        print(f"Error: Input file does not exist: {input_path}", file=sys.stderr)
        sys.exit(1)

    norm_angle = parse_rotation_angle(angle)
    meta = probe_video(input_path)
    source_width = meta["width"]
    source_height = meta["height"]
    has_audio = meta["audio_codec"] is not None

    if norm_angle in (90, 270):
        new_width, new_height = source_height, source_width
    else:
        new_width, new_height = source_width, source_height

    dest = output_path or default_output(input_path, f"rotate_{norm_angle}")

    # Ensure output directory exists
    output_dir = os.path.dirname(os.path.abspath(dest))
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("Video Rotation")
    print("=" * 60)
    print(f"Input file:       {input_path}")
    print(f"Angle:            {norm_angle}° clockwise")
    print(f"Original size:    {source_width}x{source_height}")
    print(f"Target size:      {new_width}x{new_height}")
    print(f"Audio stream:     {'Preserved (lossless copy)' if has_audio else 'None'}")
    print(f"Output file:      {dest}")
    print("=" * 60)

    vf = get_rotation_filter(norm_angle)

    cmd = [
        "-i", input_path,
        "-vf", vf,
        "-metadata:s:v:0", "rotate=0",
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "medium",
    ]

    if has_audio:
        cmd.extend(["-c:a", "copy"])
    else:
        cmd.append("-an")

    cmd.append(dest)

    run_ffmpeg(cmd, desc=f"Rotating video {norm_angle}° clockwise")

    print(f"\n{'=' * 60}")
    print("Rotation complete!")
    print(f"Output saved to: {dest}")
    print(f"{'=' * 60}")
    return dest


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rotate a video by right angles (90°, 180°, or 270°).",
        epilog="""Examples:
  # Rotate 90 degrees clockwise:
  python rotate.py -i video.mp4 -a 90
  python rotate.py -i video.mp4 -a cw

  # Rotate 180 degrees (upside-down fix):
  python rotate.py -i video.mp4 -a 180

  # Rotate 90 degrees counter-clockwise (270° clockwise):
  python rotate.py -i video.mp4 -a ccw
  python rotate.py -i video.mp4 -a 270 -o rotated_ccw.mp4
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input video file path.",
    )
    parser.add_argument(
        "--angle", "-a",
        required=True,
        help="Rotation angle: 90, 180, 270 (or aliases 'cw', 'ccw', '90cw', '90ccw').",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output file path (default: <input>_rotate_<angle>.mp4).",
    )

    args = parser.parse_args()

    try:
        rotate_video(
            input_path=args.input,
            angle=args.angle,
            output_path=args.output,
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
