"""
Speed up a video (either the whole clip or specific segments) with pitch-corrected audio.

Usage examples:
    # Speed up whole video by 4x:
    python speedup.py --input video.mp4 --speed 4x
    python speedup.py -i video.mp4 --speed 2

    # Speed up specific segments while keeping the rest at normal speed:
    python speedup.py -i video.mp4 --segments 00:05:00-00:08:00@4x 00:15:00-00:17:00@4x
"""

import argparse
import os
import re
import shutil
import sys
import tempfile

from ffmpeg_utils import (
    build_atempo_chain,
    default_output,
    format_timestamp,
    parse_timestamp,
    probe_video,
    run_ffmpeg,
)

SEGMENT_REGEX = re.compile(r"^([\d:.]+)-([\d:.]+)@([\d.]+)x$", re.IGNORECASE)


def parse_speed_multiplier(speed_str: str) -> float:
    """
    Parse a speed multiplier string (e.g. '4x', '4X', '2.5', '2').
    """
    cleaned = speed_str.strip().rstrip("xX")
    try:
        speed = float(cleaned)
    except ValueError:
        print(f"Error: Invalid speed multiplier '{speed_str}'. Expected a number like 2, 4, 4x, etc.", file=sys.stderr)
        sys.exit(1)

    if speed <= 0:
        print(f"Error: Speed multiplier must be greater than 0, got {speed}", file=sys.stderr)
        sys.exit(1)

    return speed


def speedup_whole_video(
    input_path: str,
    speed: float,
    output_path: str | None = None,
) -> str:
    """
    Speed up the entire video by a constant multiplier.
    Performs a single-pass re-encode with pitch-corrected audio and consistent framerate.
    """
    if not os.path.isfile(input_path):
        print(f"Error: Input file does not exist: {input_path}", file=sys.stderr)
        sys.exit(1)

    info = probe_video(input_path)
    duration = info["duration"]
    has_audio = info["audio_codec"] is not None
    target_fps = round(info["fps"], 2)
    fps_str = f"{target_fps:g}"

    if not output_path:
        output_path = default_output(input_path, f"speed_{speed:g}x")

    output_dir = os.path.dirname(os.path.abspath(output_path))
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    new_duration = duration / speed
    print("=" * 60)
    print("Whole-Clip Video Speedup")
    print("=" * 60)
    print(f"Input file:       {input_path}")
    print(f"Original length:  {format_timestamp(duration)} ({duration:.2f}s)")
    print(f"Frame rate:       {fps_str} fps")
    print(f"Speed multiplier: {speed:g}x")
    print(f"Expected length:  ~{format_timestamp(new_duration)} ({new_duration:.2f}s)")
    print(f"Has audio:        {'Yes (' + str(info['audio_codec']) + ')' if has_audio else 'No'}")
    print(f"Output file:      {output_path}")
    print("=" * 60)

    cmd_args = [
        "-i", input_path,
        "-vf", f"setpts=PTS/{speed},fps={fps_str}",
        "-r", fps_str,
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "medium",
    ]

    if has_audio:
        cmd_args += ["-af", build_atempo_chain(speed), "-c:a", "aac", "-b:a", "192k"]
    else:
        cmd_args += ["-an"]

    cmd_args.append(output_path)
    run_ffmpeg(cmd_args, desc=f"Speeding up entire video by {speed:g}x")

    print("\n" + "=" * 60)
    print("Completed successfully!")
    print(f"Output saved to: {output_path}")
    print("=" * 60)
    return output_path


def parse_segment(seg_str: str) -> tuple[float, float, float]:
    """
    Parse a segment string in the format START-END@MULTIPLIERx.

    Returns:
        tuple of (start_seconds, end_seconds, speed_multiplier)
    """
    match = SEGMENT_REGEX.match(seg_str.strip())
    if not match:
        print(
            f"Error: Invalid segment format '{seg_str}'. "
            f"Expected format: START-END@MULTIPLIERx (e.g. 00:05:00-00:08:00@4x)",
            file=sys.stderr,
        )
        sys.exit(1)

    start_str, end_str, speed_str = match.groups()
    start = parse_timestamp(start_str)
    end = parse_timestamp(end_str)
    speed = parse_speed_multiplier(speed_str)

    if start < 0:
        print(f"Error: Segment start time cannot be negative in '{seg_str}'", file=sys.stderr)
        sys.exit(1)

    if start >= end:
        print(
            f"Error: Segment start ({format_timestamp(start)}) must be before "
            f"end ({format_timestamp(end)}) in '{seg_str}'",
            file=sys.stderr,
        )
        sys.exit(1)

    return start, end, speed


def speedup_video(
    input_path: str,
    segment_specs: list[str],
    output_path: str | None = None,
) -> str:
    """
    Process video to speed up specified segments and keep the rest at normal speed.
    """
    if not os.path.isfile(input_path):
        print(f"Error: Input file does not exist: {input_path}", file=sys.stderr)
        sys.exit(1)

    # 1. Probe input video metadata
    info = probe_video(input_path)
    duration = info["duration"]
    has_audio = info["audio_codec"] is not None
    target_fps = round(info["fps"], 2)
    fps_str = f"{target_fps:g}"

    if duration <= 0:
        print(f"Error: Unable to determine valid duration for {input_path}", file=sys.stderr)
        sys.exit(1)

    # 2. Parse and validate segment strings
    raw_segments = [parse_segment(s) for s in segment_specs]

    # 3. Sort segments by start time
    raw_segments.sort(key=lambda s: s[0])

    # 4. Validate bounds against video duration and check for overlaps
    validated_segments = []
    for start, end, speed in raw_segments:
        if start >= duration:
            print(
                f"Error: Segment start ({format_timestamp(start)}) is beyond "
                f"video duration ({format_timestamp(duration)})",
                file=sys.stderr,
            )
            sys.exit(1)

        if end > duration:
            if end - duration < 0.1:
                end = duration
            else:
                print(
                    f"Error: Segment end ({format_timestamp(end)}) exceeds "
                    f"video duration ({format_timestamp(duration)})",
                    file=sys.stderr,
                )
                sys.exit(1)

        validated_segments.append((start, end, speed))

    for i in range(1, len(validated_segments)):
        prev_start, prev_end, _ = validated_segments[i - 1]
        curr_start, curr_end, _ = validated_segments[i]
        if curr_start < prev_end:
            print(
                f"Error: Segments overlap: {format_timestamp(prev_start)}-{format_timestamp(prev_end)} "
                f"and {format_timestamp(curr_start)}-{format_timestamp(curr_end)}",
                file=sys.stderr,
            )
            sys.exit(1)

    # 5. Build list of all time ranges covering the whole video
    ranges: list[tuple[float, float, float]] = []
    current_time = 0.0

    for start, end, speed in validated_segments:
        if start > current_time:
            ranges.append((current_time, start, 1.0))
        ranges.append((start, end, speed))
        current_time = end

    if current_time < duration:
        ranges.append((current_time, duration, 1.0))

    # Skip zero-duration ranges
    ranges = [(s, e, sp) for s, e, sp in ranges if (e - s) > 0.001]

    if not ranges:
        print("Error: No valid ranges to process.", file=sys.stderr)
        sys.exit(1)

    if not output_path:
        output_path = default_output(input_path, "speedup")

    output_dir = os.path.dirname(os.path.abspath(output_path))
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Print summary of segments
    print("=" * 60)
    print("Video Segment Speedup Plan")
    print("=" * 60)
    print(f"Input file:     {input_path}")
    print(f"Total duration: {format_timestamp(duration)} ({duration:.2f}s)")
    print(f"Frame rate:     {fps_str} fps")
    print(f"Has audio:      {'Yes (' + str(info['audio_codec']) + ')' if has_audio else 'No'}")
    print(f"Output file:    {output_path}")
    print("\nSped-up segments requested:")
    for start, end, speed in validated_segments:
        print(f"  • {format_timestamp(start)} - {format_timestamp(end)} @ {speed:g}x")
    print(f"\nAll timeline ranges ({len(ranges)} total):")
    for idx, (s, e, sp) in enumerate(ranges, start=1):
        label = f"SPEEDUP ({sp:g}x)" if abs(sp - 1.0) > 1e-4 else "NORMAL (1x)"
        print(f"  [{idx:02d}] {format_timestamp(s)} - {format_timestamp(e)} ({e - s:.2f}s) -> {label}")
    print("=" * 60)

    # 6. Process each range in a temporary directory
    temp_dir = tempfile.mkdtemp(prefix="speedup_")
    try:
        intermediate_files = []
        for idx, (start, end, speed) in enumerate(ranges, start=1):
            part_path = os.path.join(temp_dir, f"part_{idx:04d}.mp4")
            intermediate_files.append(part_path)

            is_fast = abs(speed - 1.0) > 1e-4
            desc = (
                f"Range {idx}/{len(ranges)}: {format_timestamp(start)} - {format_timestamp(end)} @ {speed:g}x"
                if is_fast
                else f"Range {idx}/{len(ranges)}: {format_timestamp(start)} - {format_timestamp(end)} @ 1x (normal)"
            )

            cmd_args = [
                "-ss", format_timestamp(start),
                "-to", format_timestamp(end),
                "-i", input_path,
            ]

            if is_fast:
                cmd_args += ["-vf", f"setpts=PTS/{speed},fps={fps_str}"]
                if has_audio:
                    cmd_args += ["-af", build_atempo_chain(speed)]
            else:
                cmd_args += ["-vf", f"fps={fps_str}"]

            cmd_args += [
                "-r", fps_str,
                "-c:v", "libx264",
                "-crf", "18",
                "-preset", "medium",
            ]

            if has_audio:
                cmd_args += ["-c:a", "aac", "-b:a", "192k"]
            else:
                cmd_args += ["-an"]

            cmd_args.append(part_path)
            run_ffmpeg(cmd_args, desc=desc)

        # 7. Create concat demuxer file
        concat_txt = os.path.join(temp_dir, "concat.txt")
        with open(concat_txt, "w") as f:
            for p in intermediate_files:
                safe_path = p.replace("'", "'\\''")
                f.write(f"file '{safe_path}'\n")

        # 8. Concatenate all segments using concat demuxer:
        # Since all parts have identical resolution, codec, and normalized FPS, video stream copy is seamless.
        # Re-encoding audio during final assembly prevents packet-boundary timestamp jitter across cuts.
        concat_args = [
            "-f", "concat",
            "-safe", "0",
            "-i", concat_txt,
            "-c:v", "copy",
        ]
        if has_audio:
            concat_args += ["-c:a", "aac", "-b:a", "192k"]
        else:
            concat_args += ["-an"]
        concat_args.append(output_path)
        run_ffmpeg(concat_args, desc="Concatenating all segments into final output")

    finally:
        # 9. Clean up temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)

    print("\n" + "=" * 60)
    print("Completed successfully!")
    print(f"Output saved to: {output_path}")
    print("=" * 60)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Speed up a video with pitch-corrected audio (whole clip or specific segments).",
        epilog="""Examples:
  # Speed up whole clip:
  python speedup.py --input video.mp4 --speed 4x
  python speedup.py -i video.mp4 --speed 2 -o fast.mp4

  # Speed up specific segments:
  python speedup.py --input video.mp4 --segments 00:05:00-00:08:00@4x 00:15:00-00:17:00@8x
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Input video file path",
    )
    parser.add_argument(
        "--speed", "-m",
        default=None,
        help="Speed up entire video by multiplier (e.g. '2', '4x', '8x'). No timestamps needed.",
    )
    parser.add_argument(
        "-s", "--segments",
        nargs="+",
        default=None,
        help="Space-separated list of START-END@MULTIPLIERx strings (e.g. 00:05:00-00:08:00@4x)",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output file path (default: auto-generated filename)",
    )

    args = parser.parse_args()

    if args.speed and args.segments:
        parser.error("Specify either --speed (whole clip) OR --segments (specific intervals), not both.")

    if not args.speed and not args.segments:
        parser.error("Either --speed (for whole clip) or --segments (for specific ranges) is required.")

    if args.speed:
        speed_val = parse_speed_multiplier(args.speed)
        speedup_whole_video(
            input_path=args.input,
            speed=speed_val,
            output_path=args.output,
        )
    else:
        speedup_video(
            input_path=args.input,
            segment_specs=args.segments,
            output_path=args.output,
        )


if __name__ == "__main__":
    main()
