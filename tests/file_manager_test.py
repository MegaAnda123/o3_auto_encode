import re
from pathlib import Path

from o3_auto_encode import file_manager

TEST_ROOT = Path(__file__).parent


def test_generate_bundles() -> None:
    path = TEST_ROOT / "test_files/144p"

    bundles = file_manager.generate_bundles(path)

    clips = [
        file_manager.Clip.from_path(path / "DJI_0237.MP4"),
        file_manager.Clip.from_path(path / "DJI_0238.MP4"),
        file_manager.Clip.from_path(path / "DJI_0239.MP4"),
        file_manager.Clip.from_path(path / "DJI_0240.MP4"),
    ]

    expected = [
        file_manager.Bundle(clips[0:2]),
        file_manager.Bundle(clips[2:4]),
    ]

    for result_bundle, expected_bundle in zip(bundles, expected):
        assert result_bundle.name == expected_bundle.name
        assert result_bundle.creation_time == expected_bundle.creation_time
        for result_clip, expected_clip in zip(result_bundle.clips, expected_bundle.clips):
            assert result_clip.name == expected_clip.name
            assert result_clip.duration == expected_clip.duration
            assert result_clip.path == expected_clip.path
            assert result_clip.creation_time == expected_clip.creation_time
            assert result_clip.creation_time_unix == expected_clip.creation_time_unix
            assert result_clip.duration_s == expected_clip.duration_s


def test_json_serialization() -> None:
    clip_path = TEST_ROOT / "test_files/144p/DJI_0237.MP4"
    clip = file_manager.Clip.from_path(clip_path)

    result = clip.__dict__()

    expected = {
        "name": "DJI_0237.MP4",
        "duration": "00:03:14.73",
        "path": str(clip_path.absolute()),
        "creation_time": "2024-05-16T15:21:44.000000Z",
        "creation_time_unix": 1715872904.0,
        "duration_s": 194.73,
        "delta": None,
        "frames": 11672,
    }

    for key, value in expected.items():
        assert result[key] == value


def test_clip_probe_stats() -> None:
    clip_path = TEST_ROOT / "test_files/144p/DJI_0237.MP4"

    clip = file_manager.Clip.from_path(clip_path)

    assert clip.size == clip_path.stat().st_size
    assert re.fullmatch(r"\d+x\d+", clip.resolution)
    assert clip.bitrate > 0
    assert clip.fps > 0
    assert clip.codec


def test_bundle_totals() -> None:
    path = TEST_ROOT / "test_files/144p"
    clips = [
        file_manager.Clip.from_path(path / "DJI_0237.MP4"),
        file_manager.Clip.from_path(path / "DJI_0238.MP4"),
    ]

    bundle = file_manager.Bundle(clips)

    assert bundle.total_frames == sum(clip.frames for clip in clips)
    assert bundle.total_size == sum(clip.size for clip in clips)
    assert bundle.encoded is None
    assert bundle.is_encoded is False
    assert bundle.output_path("/tmp/out") == Path("/tmp/out") / bundle.name


def test_bundle_output_path_prefers_config() -> None:
    path = TEST_ROOT / "test_files/144p"
    bundle = file_manager.Bundle([file_manager.Clip.from_path(path / "DJI_0237.MP4")])
    bundle.config = {"output": "/configured"}

    assert bundle.output_path("/fallback") == Path("/configured") / bundle.name

