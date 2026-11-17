#!/usr/bin/env python3
"""
Crop a landscape video (1920x1080) to portrait (9:16) or landscape (16:9) format.

Supports:
- Full-bleed portrait crop (default center crop down to 9:16)
- Custom left/right crop with top and bottom filled with:
  • Blurred video background ('blur' / 'shadow')
  • Solid black bars ('black')

Usage examples:
    # Full bleed center crop to 9:16:
    python crop.py --input video.mp4 --format portrait

    # Crop 200px from left and 150px from right, fill top/bottom with blurred video:
    python crop.py -i video.mp4 -f portrait --crop-left 200 --crop-right 150 --fill blur

    # Crop left/right and fill top/bottom with black bars:
    python crop.py -i video.mp4 -f portrait --crop-left 200 --crop-right 200 --fill black

    # Keep entire 16:9 width without cropping, fill top/bottom with blurred video background:
    python crop.py -i video.mp4 -f portrait --fill blur
"""

import argparse
import sys

from ffmpeg_utils import (
    FORMAT_PRESETS,
    default_output,
    ensure_even,
    format_timestamp,
    probe_video,
    run_ffmpeg,
)


def crop_video(
    input_path: str,
    target_format: str,
    crop_x: int = 0,
    crop_left: int = 0,
    crop_right: int = 0,
    crop_top: int = 0,
    crop_bottom: int = 0,
    fill: str | None = None,
    max_duration: float | None = None,
    output_path: str | None = None,
) -> str:
    """
    Crop and format a video to portrait or landscape.

    Args:
        input_path: Path to the input video file.
        target_format: Target format ('portrait' or 'landscape').
        crop_x: Horizontal offset from center in pixels for full-bleed crop.
        crop_left: Pixels to crop from left edge.
        crop_right: Pixels to crop from right edge.
        crop_top: Pixels to crop from top edge.
        crop_bottom: Pixels to crop from bottom edge.
        fill: Fill style for top & bottom in portrait ('blur', 'shadow', 'black', or 'none').
        max_duration: Maximum output duration in seconds. Trims if exceeded.
        output_path: Output file path. Defaults to auto-generated path if None.

    Returns:
        The output file path.
    """
    meta = probe_video(input_path)
    source_width = meta["width"]
    source_height = meta["height"]
    duration = meta["duration"]
    has_audio = meta["audio_codec"] is not None

    if target_format == "portrait" and duration > 60 and max_duration is None:
        print(f"⚠ Output is {duration:.0f}s. YouTube Shorts max is 60s. Use --max-duration 60 to auto-trim.")

    dest = output_path or default_output(input_path, target_format)

    # Determine if fill mode (letterbox with black or blurred video background) should be used
    has_custom_crop = (crop_left > 0 or crop_right > 0 or crop_top > 0 or crop_bottom > 0)
    use_fill = (fill is not None and fill != "none") or (has_custom_crop and fill != "none")

    effective_fill = fill or "blur"
    if effective_fill == "shadow":
        effective_fill = "blur"

    if target_format == "portrait":
        if use_fill and effective_fill in ("blur", "black"):
            if crop_left + crop_right >= source_width:
                print(
                    f"Error: crop_left ({crop_left}) + crop_right ({crop_right}) exceeds video width ({source_width}).",
                    file=sys.stderr,
                )
                sys.exit(1)
            if crop_top + crop_bottom >= source_height:
                print(
                    f"Error: crop_top ({crop_top}) + crop_bottom ({crop_bottom}) exceeds video height ({source_height}).",
                    file=sys.stderr,
                )
                sys.exit(1)

            crop_w = ensure_even(source_width - crop_left - crop_right)
            crop_h = ensure_even(source_height - crop_top - crop_bottom)
            crop_x_pos = crop_left
            crop_y_pos = crop_top

            scale_fg = "scale=1080:1920:force_original_aspect_ratio=decrease,scale=trunc(iw/2)*2:trunc(ih/2)*2"

            if effective_fill == "black":
                vf = (
                    f"crop={crop_w}:{crop_h}:{crop_x_pos}:{crop_y_pos},"
                    f"{scale_fg},"
                    f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black"
                )
                cmd = ["-i", input_path, "-vf", vf]
            else:  # blur / shadow
                # Background: scaled and cropped to 1080x1920, boxblurred, slightly dimmed
                # Foreground: cropped left/right, scaled to fit 1080x1920 width, centered vertically
                filter_complex = (
                    f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5,eq=brightness=-0.1[bg];"
                    f"[0:v]crop={crop_w}:{crop_h}:{crop_x_pos}:{crop_y_pos},{scale_fg}[fg];"
                    f"[bg][fg]overlay=(W-w)/2:(H-h)/2[v]"
                )
                cmd = ["-i", input_path, "-filter_complex", filter_complex, "-map", "[v]"]
                if has_audio:
                    cmd.extend(["-map", "0:a"])

        else:
            # Full-bleed 9:16 crop
            crop_w = ensure_even(int(round(source_height * 9 / 16)))
            crop_h = source_height
            crop_x_pos = int((source_width - crop_w) / 2 + crop_x)
            crop_y_pos = 0
            vf = f"crop={crop_w}:{crop_h}:{crop_x_pos}:{crop_y_pos},scale=1080:1920"
            cmd = ["-i", input_path, "-vf", vf]

    elif target_format == "landscape":
        vf = "scale=1920:1080"
        cmd = ["-i", input_path, "-vf", vf]
    else:
        raise ValueError(f"Invalid format '{target_format}'. Choose 'portrait' or 'landscape'.")

    cmd.extend([
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "medium",
    ])

    if has_audio:
        cmd.extend(["-c:a", "aac", "-b:a", "192k"])
    else:
        cmd.append("-an")

    if max_duration is not None:
        duration_str = str(int(max_duration)) if max_duration == int(max_duration) else str(max_duration)
        cmd.extend(["-t", duration_str])

    cmd.append(dest)

    desc = f"Cropping to {target_format}"
    if target_format == "portrait" and use_fill:
        desc += f" (fill: {effective_fill}, crop: L={crop_left} R={crop_right})"

    run_ffmpeg(cmd, desc=desc)
    print(f"Output: {dest}")
    return dest


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Crop a landscape video (1920x1080) to portrait (9:16) or landscape (16:9) format.",
        epilog="""Examples:
  # Full bleed portrait crop:
  python crop.py -i video.mp4 -f portrait

  # Crop left & right edges, fill top & bottom with blurred video shadow:
  python crop.py -i video.mp4 -f portrait --crop-left 200 --crop-right 150 --fill blur

  # Crop left & right edges, fill top & bottom with black bars:
  python crop.py -i video.mp4 -f portrait --crop-left 200 --crop-right 150 --fill black

  # Fill top/bottom with blur without cutting sides (keep full 16:9 width):
  python crop.py -i video.mp4 -f portrait --fill blur
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input video file path.",
    )
    parser.add_argument(
        "--format", "-f",
        required=True,
        choices=["portrait", "landscape"],
        help="Target format ('portrait' or 'landscape').",
    )
    parser.add_argument(
        "--crop-left",
        type=int,
        default=0,
        help="Pixels to crop from left edge. Default: 0.",
    )
    parser.add_argument(
        "--crop-right",
        type=int,
        default=0,
        help="Pixels to crop from right edge. Default: 0.",
    )
    parser.add_argument(
        "--crop-top",
        type=int,
        default=0,
        help="Pixels to crop from top edge. Default: 0.",
    )
    parser.add_argument(
        "--crop-bottom",
        type=int,
        default=0,
        help="Pixels to crop from bottom edge. Default: 0.",
    )
    parser.add_argument(
        "--fill",
        choices=["blur", "shadow", "black", "none"],
        default=None,
        help="How to fill top & bottom in portrait: 'blur'/'shadow' (blurred video background) or 'black'. Default is 'blur' when crop-left/right is specified.",
    )
    parser.add_argument(
        "--crop-x",
        type=int,
        default=0,
        help="Horizontal offset from center in pixels for full-bleed crop (positive = right, negative = left). Default: 0.",
    )
    parser.add_argument(
        "--max-duration",
        type=float,
        default=None,
        help="Maximum output duration in seconds. Trims if exceeded.",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output file path. Default: auto-generated using default_output(input, format_name).",
    )

    args = parser.parse_args()
    crop_video(
        input_path=args.input,
        target_format=args.format,
        crop_x=args.crop_x,
        crop_left=args.crop_left,
        crop_right=args.crop_right,
        crop_top=args.crop_top,
        crop_bottom=args.crop_bottom,
        fill=args.fill,
        max_duration=args.max_duration,
        output_path=args.output,
    )


if __name__ == "__main__":
    main()
