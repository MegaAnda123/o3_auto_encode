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
    ],
)
def test_ffmpeg_settings(file: str, expected: dict[str, Any]):
    test_path = TEST_ROOT / file

    ffmpeg_settings = FFMPEGSettings.from_json(test_path)

    assert ffmpeg_settings.codec == expected["codec"]
    assert ffmpeg_settings.crf == expected["crf"]
    assert ffmpeg_settings.preset == expected["preset"]
    assert ffmpeg_settings.concatenation == expected["concatenation"]
    assert ffmpeg_settings.input == expected["input"]
    assert ffmpeg_settings.output == expected["output"]
