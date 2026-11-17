#!/usr/bin/env python3
"""
Pipeline script that chains multiple video editing operations in a single command.

Operations are applied in order: cut → speedup → crop.

Usage examples:
    python pipeline.py --input video.mp4 --cut 00:01:00-00:05:00 --crop portrait
    python pipeline.py --input video.mp4 --crop portrait --crop-left 200 --crop-right 150 --fill blur
    python pipeline.py --input video.mp4 --speedup 4x --crop portrait --fill blur
"""

import argparse
import os
import re
import shutil
import sys
import tempfile

from ffmpeg_utils import parse_rotation_angle, parse_timestamp

# Import the core functions from each script
from cut import cut_multiple_periods, parse_cut_range
from crop import crop_video
from rotate import rotate_video
from speedup import parse_speed_multiplier, speedup_video, speedup_whole_video


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Chain multiple video editing operations in a single command. "
        "Operations are applied in order: cut → rotate → speedup → crop.",
        epilog="""Examples:
  # Cut a range and crop to portrait with blurred video background:
  python pipeline.py --input video.mp4 --cut 00:01:00-00:05:00 --crop portrait --crop-left 200 --crop-right 150 --fill blur

  # Rotate 90 degrees clockwise and speed up 4x:
  python pipeline.py --input video.mp4 --rotate 90 --speedup 4x

  # Cut, rotate 90 degrees, speed up 2x, and crop to portrait:
  python pipeline.py -i video.mp4 --cut 12-37 --rotate 90 --speedup 2x --crop portrait --fill blur
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input video file path.",
    )
    parser.add_argument(
        "--cut",
        nargs="+",
        default=None,
        help="One or more cut ranges as START-END (e.g. 00:01:00-00:05:00). If multiple cuts are given, they are stitched together.",
    )
    parser.add_argument(
        "--rotate",
        default=None,
        help="Rotate video by right angles: 90, 180, 270 (or aliases 'cw', 'ccw', '90cw', '90ccw').",
    )
    parser.add_argument(
        "--speedup",
        nargs="+",
        default=None,
        help="Speed multiplier for whole video (e.g. '4x', '2') OR specific segments (e.g. '00:00:30-00:01:30@4x').",
    )
    parser.add_argument(
        "--crop",
        choices=["portrait", "landscape"],
        default=None,
        help="Crop to target format: 'portrait' (9:16) or 'landscape' (16:9).",
    )
    parser.add_argument(
        "--crop-left",
        type=int,
        default=0,
        help="Pixels to crop from left edge in portrait mode. Default: 0.",
    )
    parser.add_argument(
        "--crop-right",
        type=int,
        default=0,
        help="Pixels to crop from right edge in portrait mode. Default: 0.",
    )
    parser.add_argument(
        "--crop-top",
        type=int,
        default=0,
        help="Pixels to crop from top edge in portrait mode. Default: 0.",
    )
    parser.add_argument(
        "--crop-bottom",
        type=int,
        default=0,
        help="Pixels to crop from bottom edge in portrait mode. Default: 0.",
    )
    parser.add_argument(
        "--fill",
        choices=["blur", "shadow", "black", "none"],
        default=None,
        help="How to fill top & bottom in portrait: 'blur'/'shadow' (blurred video background) or 'black'.",
    )
    parser.add_argument(
        "--crop-x",
        type=int,
        default=0,
        help="Horizontal crop offset from center in pixels for full-bleed crop. Default: 0.",
    )
    parser.add_argument(
        "--max-duration",
        type=float,
        default=None,
        help="Maximum output duration in seconds. Trims the final output if exceeded.",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output file path. Default: auto-generated based on operations applied.",
    )

    args = parser.parse_args()

    # Validate rotation angle if provided
    rotate_angle = None
    if args.rotate:
        try:
            rotate_angle = parse_rotation_angle(args.rotate)
        except ValueError as e:
            parser.error(str(e))

    # Validate that at least one operation is specified
    if not any([args.cut, rotate_angle, args.speedup, args.crop]):
        parser.error("At least one operation (--cut, --rotate, --speedup, --crop) must be specified.")

    if not os.path.isfile(args.input):
        print(f"Error: Input file '{args.input}' not found.", file=sys.stderr)
        sys.exit(1)

    # Determine which operations to perform
    operations = []
    if args.cut:
        operations.append("cut")
    if rotate_angle:
        operations.append(f"rotate_{rotate_angle}")
    if args.speedup:
        operations.append("speedup")
    if args.crop:
        operations.append("crop")

    print("=" * 60)
    print("Pipeline Plan")
    print("=" * 60)
    print(f"Input:      {args.input}")
    print(f"Operations: {' → '.join(operations)}")
    if args.output:
        print(f"Output:     {args.output}")
    print("=" * 60)

    # Build a suffix for the default output name
    suffix_parts = []
    if args.cut:
        suffix_parts.append("cut")
    if rotate_angle:
        suffix_parts.append(f"rotate_{rotate_angle}")
    if args.speedup:
        suffix_parts.append("speedup")
    if args.crop:
        suffix_parts.append(args.crop)
    default_suffix = "_".join(suffix_parts)

    # Use a temp directory for intermediate files
    temp_dir = tempfile.mkdtemp(prefix="pipeline_")
    current_file = args.input
    step = 0

    try:
        # ── Step 1: Cut ──────────────────────────────────────────
        if args.cut:
            step += 1
            print(f"\n{'─' * 60}")
            print(f"Step {step}: Cut ({len(args.cut)} range{'s' if len(args.cut) > 1 else ''})")
            print(f"{'─' * 60}")

            cut_ranges = []
            for c in args.cut:
                s_str, e_str = parse_cut_range(c)
                cut_ranges.append((parse_timestamp(s_str), parse_timestamp(e_str)))

            # If this is the last step, output to final destination
            if step == len(operations):
                out = args.output or _default_out(args.input, default_suffix)
            else:
                out = os.path.join(temp_dir, f"step_{step}_cut.mp4")

            # Always merge multiple cut segments so downstream steps have a single video stream
            result = cut_multiple_periods(
                input_path=current_file,
                ranges=cut_ranges,
                merge=True,
                output_path=out,
            )
            current_file = result if isinstance(result, str) else result[0]

        # ── Step 2: Rotate ───────────────────────────────────────
        if rotate_angle:
            step += 1
            print(f"\n{'─' * 60}")
            print(f"Step {step}: Rotate ({rotate_angle}° clockwise)")
            print(f"{'─' * 60}")

            if step == len(operations):
                out = args.output or _default_out(args.input, default_suffix)
            else:
                out = os.path.join(temp_dir, f"step_{step}_rotate.mp4")

            current_file = rotate_video(current_file, rotate_angle, out)

        # ── Step 3: Speedup ──────────────────────────────────────
        if args.speedup:
            step += 1
            print(f"\n{'─' * 60}")
            print(f"Step {step}: Speedup")
            print(f"{'─' * 60}")

            if step == len(operations):
                out = args.output or _default_out(args.input, default_suffix)
            else:
                out = os.path.join(temp_dir, f"step_{step}_speedup.mp4")

            # Check if user specified a single multiplier for the whole clip (e.g. '4x' or '2')
            is_whole_clip = (
                len(args.speedup) == 1
                and bool(re.match(r"^[\d.]+[xX]?$", args.speedup[0].strip()))
            )

            if is_whole_clip:
                speed_val = parse_speed_multiplier(args.speedup[0])
                current_file = speedup_whole_video(current_file, speed_val, out)
            else:
                current_file = speedup_video(current_file, args.speedup, out)

        # ── Step 4: Crop ─────────────────────────────────────────
        if args.crop:
            step += 1
            print(f"\n{'─' * 60}")
            print(f"Step {step}: Crop ({args.crop})")
            print(f"{'─' * 60}")

            out = args.output or _default_out(args.input, default_suffix)
            current_file = crop_video(
                current_file,
                target_format=args.crop,
                crop_x=args.crop_x,
                crop_left=args.crop_left,
                crop_right=args.crop_right,
                crop_top=args.crop_top,
                crop_bottom=args.crop_bottom,
                fill=args.fill,
                max_duration=args.max_duration,
                output_path=out,
            )

    finally:
        # Clean up intermediate temp files
        shutil.rmtree(temp_dir, ignore_errors=True)

    print(f"\n{'=' * 60}")
    print("Pipeline complete!")
    print(f"Final output: {current_file}")
    print(f"{'=' * 60}")


def _default_out(input_path: str, suffix: str) -> str:
    """Generate a default output path."""
    from ffmpeg_utils import default_output
    return default_output(input_path, suffix)


if __name__ == "__main__":
    main()
