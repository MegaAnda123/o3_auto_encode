import subprocess
from pathlib import Path

import pytest

from o3_auto_encode import main, utils
from o3_auto_encode.args_parser import LaunchArguments

TEST_ROOT = Path(__file__).parent


@pytest.mark.parametrize(
    "args, expected",
    [
        (
            LaunchArguments(str(TEST_ROOT / "test_files/144p"), "", "", 50, "fast"),
            [
                ("DJI_0237_2024-05-16.mp4", "Duration: 00:04:10.02"),
                ("DJI_0239_2024-05-16.mp4", "Duration: 00:04:47.89"),
            ],
        )
    ],
)
def test_main(tmp_path, args: LaunchArguments, expected: list[tuple[str, str]]):
    args.output_folder = tmp_path
    args.json_path = tmp_path / "test.json"

    main.run(args)

    # Check duration on output match expected values using ffprobe.
    for video, expected_str in expected:
        path = tmp_path / video
        process = subprocess.run([utils.get_ffprobe_path(), str(path)], capture_output=True)
        result = process.stderr.decode("utf-8")
        assert expected_str in result
