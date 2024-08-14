from pathlib import Path
from typing import Any

import pytest

from o3_auto_encode.enums import Codec, EncodePreset
from o3_auto_encode.ffmpeg_settings import FFMPEGSettings

TEST_ROOT = Path(__file__).parent


@pytest.mark.parametrize(
    "file, expected",
    [
        (
            "test_files/ffmpeg_configs/test_config_1.json",
            {
                "codec": Codec.X264,
                "crf": 50,
                "preset": EncodePreset.FAST,
                "concatenation": True,
                "input": None,
                "output": None,
            },
        ),
        (
            "test_files/ffmpeg_configs/test_config_2.json",
            {
                "codec": Codec.X265,
                "crf": 5,
                "preset": EncodePreset.SLOW,
                "concatenation": True,
                "input": Path("test_files/144p"),
                "output": Path("/out"),
            },
        ),
        (
            "test_files/ffmpeg_configs/test_config_1.yaml",
            {
                "codec": Codec.X265,
                "crf": 5,
                "preset": EncodePreset.SLOW,
                "concatenation": True,
                "input": Path("test_files/144p"),
                "output": Path("/out"),
            },
        ),
        (
            "test_files/ffmpeg_configs/test_config_2.yml",
            {
                "codec": Codec.X265,
                "crf": 5,
                "preset": EncodePreset.SLOW,
                "concatenation": True,
                "input": Path("test_files/144p"),
                "output": Path("/out"),
            },
        ),
    ],
)
def test_ffmpeg_settings(file: str, expected: dict[str, Any]):
    test_path = TEST_ROOT / file

    ffmpeg_settings = FFMPEGSettings(test_path)

    assert ffmpeg_settings.codec == expected["codec"]
    assert ffmpeg_settings.crf == expected["crf"]
    assert ffmpeg_settings.preset == expected["preset"]
    assert ffmpeg_settings.concatenation == expected["concatenation"]
    assert ffmpeg_settings.input == expected["input"]
    assert ffmpeg_settings.output == expected["output"]


@pytest.mark.parametrize("suffix", [".mp4", ".avi", ".flv", ".mkv"])
def test_errors(tmp_path, suffix):
    with pytest.raises(FileNotFoundError):
        FFMPEGSettings(f"file{suffix}")

    path = Path(tmp_path) / f"file{suffix}"
    open(path, "w").close()

    with pytest.raises(ValueError, match=f"Unsupported file type `{suffix}`."):
        FFMPEGSettings(str(path))
    with pytest.raises(ValueError, match=f"Unsupported file type `{suffix}`."):
        FFMPEGSettings(path)


def test_ffmpeg_settings_no_path():
    ffmpeg_settings = FFMPEGSettings()

    ffmpeg_settings.codec = Codec.X264
    ffmpeg_settings.crf = 50
    ffmpeg_settings.preset = EncodePreset.SLOW
    ffmpeg_settings.concatenation = False

    assert ffmpeg_settings.codec == Codec.X264
    assert ffmpeg_settings.crf == 50
    assert ffmpeg_settings.preset == EncodePreset.SLOW
    assert ffmpeg_settings.concatenation is False
