"""
Merge multiple video files into one using FFmpeg.

Uses the fast, lossless concat demuxer when all input videos share the same
codec, resolution, pixel format, timebase, and audio format. Automatically falls
back to re-encoding via the concat filter when streams differ (e.g. mixing raw clips
with rotated or edited clips).

Usage:
    python merge.py --inputs clip1.mp4 clip2.mp4 clip3.mp4
    python merge.py -i clip1.mp4 clip2.mp4 -o final.mp4
    python merge.py -i clip1.mp4 clip2.mp4 --reencode -o final.mp4
"""

import argparse
import os
import sys
import tempfile

from ffmpeg_utils import probe_video, run_ffmpeg


def merge_videos(
    inputs: list[str],
    output: str | None = None,
    reencode: bool = False,
) -> str:
    """
    Merge multiple video files into a single output video.

    Args:
        inputs: List of file paths to input videos (at least 2 required).
        output: Destination file path. If None, defaults to 'merged.mp4' in
                the directory of the first input file.
        reencode: If True, forces re-encoding via concat filter even if streams
                  appear compatible.

    Returns:
        The path to the merged output video file.
    """
    if len(inputs) < 2:
        print("Error: At least 2 input files are required to merge.", file=sys.stderr)
        sys.exit(1)

    for inp in inputs:
        if not os.path.isfile(inp):
            print(f"Error: Input file does not exist: {inp}", file=sys.stderr)
            sys.exit(1)

    # Determine default output path if not specified
    if not output:
        first_input_dir = os.path.dirname(os.path.abspath(inputs[0]))
        output = os.path.join(first_input_dir, "merged.mp4")

    # Probe all inputs to check compatibility
    probed_info = [probe_video(inp) for inp in inputs]
    first_info = probed_info[0]

    # Stricter compatibility check for lossless stream copy:
    # Requires matching codecs, resolution, pixel format, timebase, FPS, and audio params.
    compatible = not reencode and all(
        info["video_codec"] == first_info["video_codec"]
        and info["width"] == first_info["width"]
        and info["height"] == first_info["height"]
        and info.get("pix_fmt") == first_info.get("pix_fmt")
        and info.get("time_base") == first_info.get("time_base")
        and abs(info["fps"] - first_info["fps"]) < 0.05
        and info["audio_codec"] == first_info["audio_codec"]
        and info.get("audio_sample_rate") == first_info.get("audio_sample_rate")
        and info.get("audio_channels") == first_info.get("audio_channels")
        for info in probed_info[1:]
    )

    if compatible:
        # Concat demuxer approach (fast, lossless stream copy)
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False, encoding="utf-8"
            ) as tf:
                temp_file = tf.name
                for inp in inputs:
                    abs_path = os.path.abspath(inp).replace("'", "'\\''")
                    tf.write(f"file '{abs_path}'\n")

            ffmpeg_args = [
                "-f", "concat",
                "-safe", "0",
                "-i", temp_file,
                "-c", "copy",
                output,
            ]
            run_ffmpeg(
                ffmpeg_args,
                desc=f"Merging {len(inputs)} files (concat demuxer, lossless)",
            )
        finally:
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)
    else:
        # Concat filter with re-encoding (robust against differing timebases, resolutions, or formats)
        n = len(inputs)
        ffmpeg_args = []
        for inp in inputs:
            ffmpeg_args.extend(["-i", inp])

        target_w = first_info["width"]
        target_h = first_info["height"]
        target_fps = round(first_info["fps"], 2)

        has_any_audio = any(info["audio_codec"] is not None for info in probed_info)
        all_same_res = all(
            info["width"] == target_w and info["height"] == target_h
            for info in probed_info
        )

        filter_parts = []
        for i, info in enumerate(probed_info):
            # Video normalization: timebase, framerate, SAR, and scaling if dimensions differ
            v_filters = [f"fps={target_fps}", "settb=AVTB", "setsar=1"]
            if not all_same_res:
                v_filters.append(
                    f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,"
                    f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2"
                )
            filter_parts.append(f"[{i}:v]{','.join(v_filters)}[v{i}]")

            # Audio normalization
            if has_any_audio:
                if info["audio_codec"] is not None:
                    filter_parts.append(
                        f"[{i}:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,aresample=async=1[a{i}]"
                    )
                else:
                    # Generate silent audio track for clips that have no audio
                    dur = info["duration"]
                    filter_parts.append(
                        f"anullsrc=channel_layout=stereo:sample_rate=48000:duration={dur}[a{i}]"
                    )

        if has_any_audio:
            concat_inputs = "".join(f"[v{i}][a{i}]" for i in range(n))
            filter_parts.append(f"{concat_inputs}concat=n={n}:v=1:a=1[outv][outa]")
        else:
            concat_inputs = "".join(f"[v{i}]" for i in range(n))
            filter_parts.append(f"{concat_inputs}concat=n={n}:v=1:a=0[outv]")

        ffmpeg_args.extend([
            "-filter_complex", ";".join(filter_parts),
            "-map", "[outv]",
        ])
        if has_any_audio:
            ffmpeg_args.extend(["-map", "[outa]"])

        ffmpeg_args.extend([
            "-c:v", "libx264",
            "-crf", "18",
            "-preset", "medium",
        ])

        if has_any_audio:
            ffmpeg_args.extend(["-c:a", "aac", "-b:a", "192k"])
        else:
            ffmpeg_args.append("-an")

        ffmpeg_args.append(output)

        run_ffmpeg(
            ffmpeg_args,
            desc=f"Merging {n} files (concat filter, re-encoding)",
        )

    print(f"Successfully merged {len(inputs)} files into {output}")
    return output


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Merge multiple video files into one using FFmpeg."
    )
    parser.add_argument(
        "-i", "--inputs",
        nargs="+",
        required=True,
        help="List of input video file paths in order.",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output file path (default: merged.mp4 in the directory of the first input file).",
    )
    parser.add_argument(
        "-r", "--reencode",
        action="store_true",
        help="Force re-encoding via concat filter (use when mixing clips from different sources).",
    )
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    merge_videos(args.inputs, args.output, reencode=args.reencode)


if __name__ == "__main__":
    main()
