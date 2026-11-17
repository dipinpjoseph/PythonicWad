#!/usr/bin/env python3
"""
Extract subclip(s) from a video using FFmpeg stream copy (lossless, no re-encoding).

Supports single or multiple time periods. When multiple periods are specified,
they can either be exported as separate clip files or merged into a single video.

Usage examples:
    # Single cut:
    python cut.py --input video.mp4 --start 00:01:30 --end 00:05:00
    python cut.py -i video.mp4 --cuts 00:01:30-00:05:00

    # Multiple cuts into separate files:
    python cut.py -i video.mp4 --cuts 00:01:00-00:02:00 00:05:00-00:07:00

    # Multiple cuts merged into one continuous video:
    python cut.py -i video.mp4 --cuts 12-37 57-186 252-517 --merge
"""

import argparse
import os
import shutil
import sys
import tempfile

from ffmpeg_utils import (
    default_output,
    format_timestamp,
    parse_timestamp,
    run_ffmpeg,
)


def safe_timestamp(seconds: float) -> str:
    """
    Convert seconds into a filesystem-safe string representation.

    Examples:
        5.0    → '0m05s'
        90.0   → '1m30s'
        3665.0 → '1h01m05s'
        5.5    → '0m05.5s'
    """
    total_seconds = seconds
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    secs = total_seconds % 60

    if secs == int(secs):
        s_part = f"{int(secs):02d}s"
    else:
        s_part = f"{secs:06.3f}".rstrip("0").rstrip(".") + "s"
        if len(s_part.split(".")[0]) == 1:
            s_part = "0" + s_part

    if hours > 0:
        return f"{hours}h{minutes:02d}m{s_part}"
    return f"{minutes}m{s_part}"


def parse_cut_range(cut_str: str) -> tuple[str, str]:
    """
    Parse a cut range string like 'START-END' into (start, end) timestamp strings.
    Handles colon timestamps like '00:01:00-00:05:00' or raw seconds like '12-37'.
    """
    separators = []
    for i, ch in enumerate(cut_str):
        if ch == '-' and i > 0 and i < len(cut_str) - 1:
            if cut_str[i - 1].isdigit() and cut_str[i + 1].isdigit():
                separators.append(i)

    if not separators:
        print(
            f"Error: Invalid cut range '{cut_str}'. Expected format: START-END (e.g. 00:01:00-00:05:00 or 12-37)",
            file=sys.stderr,
        )
        sys.exit(1)

    sep_idx = separators[-1]
    return cut_str[:sep_idx], cut_str[sep_idx + 1:]


def cut_single_clip(
    input_path: str,
    start_sec: float,
    end_sec: float,
    output_path: str,
) -> str:
    """
    Extract a single subclip using FFmpeg stream copy.
    """
    duration = end_sec - start_sec
    ffmpeg_args = [
        "-ss", format_timestamp(start_sec),
        "-i", input_path,
        "-to", format_timestamp(duration),
        "-c", "copy",
        "-avoid_negative_ts", "make_zero",
        output_path,
    ]
    run_ffmpeg(
        ffmpeg_args,
        desc=f"Cutting {input_path} ({format_timestamp(start_sec)} to {format_timestamp(end_sec)})",
    )
    return output_path


def cut_video(
    input_path: str,
    start: str,
    end: str,
    output_path: str | None = None,
) -> str:
    """
    Convenience function to cut a single range from a video.
    """
    if not os.path.exists(input_path):
        print(f"Error: Input file '{input_path}' not found.", file=sys.stderr)
        sys.exit(1)

    start_sec = parse_timestamp(start)
    end_sec = parse_timestamp(end)

    if start_sec < 0:
        print(f"Error: Start timestamp cannot be negative ({start}).", file=sys.stderr)
        sys.exit(1)

    if start_sec >= end_sec:
        print(
            f"Error: Start time ({start} = {start_sec}s) must be earlier than end time ({end} = {end_sec}s).",
            file=sys.stderr,
        )
        sys.exit(1)

    if output_path is None:
        start_str = safe_timestamp(start_sec)
        end_str = safe_timestamp(end_sec)
        output_path = default_output(input_path, f"cut_{start_str}-{end_str}")

    return cut_single_clip(input_path, start_sec, end_sec, output_path)


def cut_multiple_periods(
    input_path: str,
    ranges: list[tuple[float, float]],
    merge: bool = False,
    output_path: str | None = None,
) -> list[str] | str:
    """
    Cut multiple periods from a video.

    Args:
        input_path: Path to input video file.
        ranges: List of (start_sec, end_sec) tuples.
        merge: If True, merges all cuts into a single video file.
               If False, outputs individual files for each period.
        output_path: Target path for merged output or single cut.

    Returns:
        List of generated clip paths (if merge=False), or path to merged file (if merge=True).
    """
    if not os.path.exists(input_path):
        print(f"Error: Input file '{input_path}' not found.", file=sys.stderr)
        sys.exit(1)

    # Validate all ranges
    for s, e in ranges:
        if s < 0 or s >= e:
            print(
                f"Error: Invalid range: start ({format_timestamp(s)}) must be non-negative and before end ({format_timestamp(e)})",
                file=sys.stderr,
            )
            sys.exit(1)

    if not merge:
        # Export as separate clips
        created_files = []
        for idx, (s, e) in enumerate(ranges, start=1):
            s_str = safe_timestamp(s)
            e_str = safe_timestamp(e)
            if output_path and len(ranges) == 1:
                dest = output_path
            elif output_path:
                base, ext = os.path.splitext(output_path)
                dest = f"{base}_part{idx:02d}{ext}"
            else:
                dest = default_output(input_path, f"cut_{s_str}-{e_str}")

            cut_single_clip(input_path, s, e, dest)
            created_files.append(dest)

        return created_files

    # Merge = True: Cut each period then concatenate using concat demuxer (lossless)
    if not output_path:
        output_path = default_output(input_path, "cut_merged")

    temp_dir = tempfile.mkdtemp(prefix="cut_merge_")
    try:
        temp_clips = []
        for idx, (s, e) in enumerate(ranges, start=1):
            temp_clip = os.path.join(temp_dir, f"part_{idx:04d}.mp4")
            cut_single_clip(input_path, s, e, temp_clip)
            temp_clips.append(temp_clip)

        # Build concat list
        concat_txt = os.path.join(temp_dir, "concat.txt")
        with open(concat_txt, "w", encoding="utf-8") as f:
            for p in temp_clips:
                abs_p = os.path.abspath(p).replace("'", "'\\''")
                f.write(f"file '{abs_p}'\n")

        # Concat demuxer stream copy
        concat_args = [
            "-f", "concat",
            "-safe", "0",
            "-i", concat_txt,
            "-c", "copy",
            output_path,
        ]
        run_ffmpeg(concat_args, desc=f"Merging {len(ranges)} cut segments into {output_path}")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract subclip(s) from a video using FFmpeg stream copy (lossless, no re-encoding).",
        epilog="""Examples:
  # Single cut using start and end:
  python cut.py -i video.mp4 --start 00:01:30 --end 00:05:00

  # Multiple cuts into separate files:
  python cut.py -i video.mp4 --cuts 00:01:00-00:02:00 00:05:00-00:07:00

  # Multiple cuts merged into one video:
  python cut.py -i video.mp4 --cuts 12-37 57-186 252-517 --merge -o combined.mp4
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input video file path.",
    )
    parser.add_argument(
        "--cuts", "-c",
        nargs="+",
        default=None,
        help="One or more cut ranges as START-END (e.g. 00:01:00-00:02:30 or 12-37).",
    )
    parser.add_argument(
        "--start", "-s",
        default=None,
        help="Start timestamp for single cut (HH:MM:SS, MM:SS, or seconds).",
    )
    parser.add_argument(
        "--end", "-e",
        default=None,
        help="End timestamp for single cut (HH:MM:SS, MM:SS, or seconds).",
    )
    parser.add_argument(
        "--merge", "-m",
        action="store_true",
        help="Merge all cut periods into a single output video (lossless stream copy).",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output file path (default: auto-generated filename).",
    )

    args = parser.parse_args()

    # Collect ranges from either --cuts or --start/--end
    ranges: list[tuple[float, float]] = []

    if args.cuts:
        for c in args.cuts:
            s_str, e_str = parse_cut_range(c)
            ranges.append((parse_timestamp(s_str), parse_timestamp(e_str)))
    elif args.start and args.end:
        ranges.append((parse_timestamp(args.start), parse_timestamp(args.end)))
    else:
        parser.error("Either --cuts START-END [START-END ...] or both --start and --end must be specified.")

    result = cut_multiple_periods(
        input_path=args.input,
        ranges=ranges,
        merge=args.merge,
        output_path=args.output,
    )

    if isinstance(result, list):
        print(f"\nGenerated {len(result)} clips:")
        for path in result:
            print(f"  • {path}")
    else:
        print(f"\nMerged output: {result}")


if __name__ == "__main__":
    main()
