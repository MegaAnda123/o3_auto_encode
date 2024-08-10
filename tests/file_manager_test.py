from pathlib import Path

from o3_auto_encode import file_manager

TEST_ROOT = Path(__file__).parent


def test_generate_bundles() -> None:
    path = TEST_ROOT / "test_files/144p"

    bundles = file_manager.generate_bundles(path)

    clips = [
        file_manager.Clip(path / "DJI_0237.MP4"),
        file_manager.Clip(path / "DJI_0238.MP4"),
        file_manager.Clip(path / "DJI_0239.MP4"),
        file_manager.Clip(path / "DJI_0240.MP4"),
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
    clip = file_manager.Clip(clip_path)

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

    assert result == expected
