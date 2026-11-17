#!/usr/bin/env python3
"""
Unit and integration tests for right-angle video rotation.
"""

import os
import shutil
import subprocess
import tempfile
import unittest

from ffmpeg_utils import (
    get_rotation_filter,
    parse_rotation_angle,
    probe_video,
)
from rotate import rotate_video


class TestRotationHelpers(unittest.TestCase):
    def test_parse_valid_integers(self):
        self.assertEqual(parse_rotation_angle(90), 90)
        self.assertEqual(parse_rotation_angle(180), 180)
        self.assertEqual(parse_rotation_angle(270), 270)
        self.assertEqual(parse_rotation_angle(450), 90)
        self.assertEqual(parse_rotation_angle(-90), 270)
        self.assertEqual(parse_rotation_angle(-180), 180)
        self.assertEqual(parse_rotation_angle(-270), 90)

    def test_parse_valid_strings(self):
        self.assertEqual(parse_rotation_angle("90"), 90)
        self.assertEqual(parse_rotation_angle("180"), 180)
        self.assertEqual(parse_rotation_angle("270"), 270)
        self.assertEqual(parse_rotation_angle("cw"), 90)
        self.assertEqual(parse_rotation_angle("ccw"), 270)
        self.assertEqual(parse_rotation_angle("90cw"), 90)
        self.assertEqual(parse_rotation_angle("90ccw"), 270)
        self.assertEqual(parse_rotation_angle("180cw"), 180)
        self.assertEqual(parse_rotation_angle("180ccw"), 180)
        self.assertEqual(parse_rotation_angle("270cw"), 270)
        self.assertEqual(parse_rotation_angle("270ccw"), 90)
        self.assertEqual(parse_rotation_angle("90 deg"), 90)
        self.assertEqual(parse_rotation_angle("180 degrees"), 180)

    def test_parse_invalid_angles(self):
        invalid_inputs = [0, 360, 45, -45, 30, "0", "45", "100", "invalid", ""]
        for val in invalid_inputs:
            with self.subTest(val=val):
                with self.assertRaises(ValueError):
                    parse_rotation_angle(val)

    def test_get_rotation_filter(self):
        self.assertEqual(get_rotation_filter(90), "transpose=1")
        self.assertEqual(get_rotation_filter(180), "hflip,vflip")
        self.assertEqual(get_rotation_filter(270), "transpose=2")
        with self.assertRaises(ValueError):
            get_rotation_filter(45)


class TestVideoRotationE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp(prefix="test_rotation_")
        cls.sample_with_audio = os.path.join(cls.temp_dir, "sample_audio.mp4")
        cls.sample_no_audio = os.path.join(cls.temp_dir, "sample_no_audio.mp4")

        # Create a synthetic 1s 320x240 test video with audio
        subprocess.run(
            [
                "ffmpeg", "-y", "-v", "error",
                "-f", "lavfi", "-i", "testsrc=duration=1:size=320x240:rate=30",
                "-f", "lavfi", "-i", "sine=frequency=1000:duration=1",
                "-c:v", "libx264", "-c:a", "aac",
                cls.sample_with_audio,
            ],
            check=True,
        )

        # Create a synthetic 1s 320x240 test video without audio
        subprocess.run(
            [
                "ffmpeg", "-y", "-v", "error",
                "-f", "lavfi", "-i", "testsrc=duration=1:size=320x240:rate=30",
                "-c:v", "libx264", "-an",
                cls.sample_no_audio,
            ],
            check=True,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_rotate_90_with_audio(self):
        out_path = os.path.join(self.temp_dir, "out_90.mp4")
        res = rotate_video(self.sample_with_audio, 90, out_path)
        self.assertEqual(res, out_path)
        self.assertTrue(os.path.isfile(out_path))

        meta = probe_video(out_path)
        self.assertEqual(meta["width"], 240)
        self.assertEqual(meta["height"], 320)
        self.assertIsNotNone(meta["audio_codec"])

    def test_rotate_180_no_audio(self):
        out_path = os.path.join(self.temp_dir, "out_180.mp4")
        res = rotate_video(self.sample_no_audio, "180", out_path)
        self.assertEqual(res, out_path)
        self.assertTrue(os.path.isfile(out_path))

        meta = probe_video(out_path)
        self.assertEqual(meta["width"], 320)
        self.assertEqual(meta["height"], 240)
        self.assertIsNone(meta["audio_codec"])

    def test_rotate_270_ccw(self):
        out_path = os.path.join(self.temp_dir, "out_270.mp4")
        res = rotate_video(self.sample_with_audio, "ccw", out_path)
        self.assertEqual(res, out_path)
        self.assertTrue(os.path.isfile(out_path))

        meta = probe_video(out_path)
        self.assertEqual(meta["width"], 240)
        self.assertEqual(meta["height"], 320)
        self.assertIsNotNone(meta["audio_codec"])

    def test_rotate_cli(self):
        out_path = os.path.join(self.temp_dir, "out_cli.mp4")
        cmd = [
            "python3", "rotate.py",
            "-i", self.sample_with_audio,
            "-a", "cw",
            "-o", out_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(os.path.isfile(out_path))
        meta = probe_video(out_path)
        self.assertEqual(meta["width"], 240)
        self.assertEqual(meta["height"], 320)

    def test_pipeline_with_rotate(self):
        out_path = os.path.join(self.temp_dir, "out_pipeline.mp4")
        cmd = [
            "python3", "pipeline.py",
            "-i", self.sample_with_audio,
            "--rotate", "90",
            "-o", out_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(os.path.isfile(out_path))
        meta = probe_video(out_path)
        self.assertEqual(meta["width"], 240)
        self.assertEqual(meta["height"], 320)

    def test_pipeline_chain_rotate_and_speedup(self):
        out_path = os.path.join(self.temp_dir, "out_pipeline_speed.mp4")
        cmd = [
            "python3", "pipeline.py",
            "-i", self.sample_with_audio,
            "--rotate", "90",
            "--speedup", "2x",
            "-o", out_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(os.path.isfile(out_path))
        meta = probe_video(out_path)
        self.assertEqual(meta["width"], 240)
        self.assertEqual(meta["height"], 320)
        self.assertAlmostEqual(meta["duration"], 0.5, delta=0.1)


    def test_merge_with_rotated_video(self):
        from merge import merge_videos
        # Rotate sample_with_audio by 180 (keeps 320x240, but has different encoder/timebase)
        rotated_180 = os.path.join(self.temp_dir, "sample_rot180.mp4")
        rotate_video(self.sample_with_audio, 180, rotated_180)

        # Merge original with rotated_180
        merged_out = os.path.join(self.temp_dir, "merged_result.mp4")
        merge_videos([self.sample_with_audio, rotated_180], merged_out)
        self.assertTrue(os.path.isfile(merged_out))
        meta = probe_video(merged_out)
        self.assertEqual(meta["width"], 320)
        self.assertEqual(meta["height"], 240)
        self.assertAlmostEqual(meta["duration"], 2.0, delta=0.2)


if __name__ == "__main__":
    unittest.main()


