import subprocess
from pathlib import Path

import pytest

from o3_auto_encode import main, utils
from o3_auto_encode.args_parser import LaunchArguments
from o3_auto_encode.db import FileDataBase
from o3_auto_encode.enums import BundleStatus

TEST_ROOT = Path(__file__).parent


@pytest.mark.parametrize(
    "expected, expected_db",
    [
        (
            [
                ("DJI_0237_2024-05-16.mp4", "Duration: 00:04:10.02"),
                ("DJI_0239_2024-05-16.mp4", "Duration: 00:04:47.89"),
            ],
            TEST_ROOT / "test_files/expected/main_expected.json",
        )
    ],
)
def test_main(helpers, tmp_path, expected: list[tuple[str, str]], expected_db: Path):
    args = LaunchArguments(str(helpers.get_test_config(tmp_path)), str(tmp_path / "test.json"))

    main.run(args)

    # Check duration on output match expected values using ffprobe.
    for video, expected_str in expected:
        path = tmp_path / video
        process = subprocess.run([utils.get_ffprobe_path(), str(path)], capture_output=True)
        result = process.stderr.decode("utf-8")
        assert expected_str in result

    helpers.test_db_files(tmp_path / "test.json", expected_db)


def test_interrupt(helpers, tmp_path, mocker):
    args = LaunchArguments(str(helpers.get_test_config(tmp_path)), str(tmp_path / "test.json"))

    with mocker.patch("o3_auto_encode.main.encode_bundle", side_effect=KeyboardInterrupt):
        main.run(args)

    result_path = tmp_path / "test.json"
    expected_path = TEST_ROOT / "test_files/expected/interrupt_expected.json"

    helpers.test_db_files(result_path, expected_path)


def test_resume_interrupted(helpers, tmp_path):
    args = LaunchArguments(str(helpers.get_test_config(tmp_path)), str(tmp_path / "test.json"))

    main.run(args)

    db = FileDataBase(tmp_path / "test.json")
    db.bundles[0].status = BundleStatus.INTERRUPTED
    db.bundles[1].status = BundleStatus.INTERRUPTED
    db.write()

    # Rerun with interrupted video in db.
    main.run(args)

    result_path = tmp_path / "test.json"
    expected_path = TEST_ROOT / "test_files/expected/main_expected.json"
    helpers.test_db_files(result_path, expected_path)
