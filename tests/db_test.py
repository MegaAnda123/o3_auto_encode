import shutil
from pathlib import Path

import pytest

from o3_auto_encode.db import FileDataBase
from o3_auto_encode.enums import BundleStatus
from o3_auto_encode.file_manager import generate_bundles

TEST_ROOT = Path(__file__).parent


@pytest.mark.parametrize(
    "file_name, expected_file",
    [
        ("test.json", "db_expected1.json"),
        ("test.yaml", "db_expected2.yaml"),
        ("test.yml", "db_expected2.yaml"),
    ],
)
def test_db(helpers, tmp_path, file_name, expected_file):
    db_path = Path(tmp_path, file_name)
    expected_path = TEST_ROOT / f"test_files/expected/{expected_file}"

    bundles = generate_bundles(TEST_ROOT / "test_files/144p/")
    db = FileDataBase(db_path)
    db.bundles = bundles
    db.write()

    helpers.test_db_files(db_path, expected_path)


@pytest.mark.parametrize(
    "file_name",
    [
        "db_expected1.json",
        "db_expected2.yaml",
    ],
)
def test_file_initialization(helpers, tmp_path, file_name):
    db_path = TEST_ROOT / f"test_files/expected/{file_name}"

    db = FileDataBase(db_path)

    result_path = Path(tmp_path, file_name)
    db.path = result_path
    db.write()

    helpers.test_db_files(result_path, db_path)


@pytest.mark.parametrize(
    "db_path, expected_path",
    [(TEST_ROOT / "test_files/data/partial_db.json", TEST_ROOT / "test_files/expected/partial_expected1.json")],
)
def test_init_with_existing_data(helpers, tmp_path, db_path: Path, expected_path: Path):
    clip_folder = TEST_ROOT / "test_files/144p/"

    tmp_db_path = Path(tmp_path, db_path.name)

    shutil.copy(db_path, tmp_db_path)
    db = FileDataBase(tmp_db_path, generate_bundles(clip_folder))
    db.write()

    helpers.test_db_files(tmp_db_path, expected_path)


def test_db_write_creates_parent_directories(tmp_path):
    db_path = tmp_path / "out" / ".meta.json"

    db = FileDataBase(db_path)
    db.write()

    assert db_path.is_file()


def test_validate_marks_bundle_verified_and_writes(tmp_path, mocker):
    bundles = generate_bundles(TEST_ROOT / "test_files/144p/")
    db_path = tmp_path / "test.json"
    db = FileDataBase(db_path, bundles)

    bundle = db.bundles[0]
    bundle.status = BundleStatus.DONE
    bundle.config = {"output": str(tmp_path)}

    expected_frames = sum(clip.frames for clip in bundle.clips)
    (tmp_path / bundle.name).touch()
    mocker.patch("o3_auto_encode.utils.get_video_frames_fast", return_value=expected_frames)

    assert db.validate() is True
    assert bundle.status == BundleStatus.VERIFIED

    persisted_db = FileDataBase(db_path)
    assert persisted_db.bundles[0].status == BundleStatus.VERIFIED


def test_validate_records_encoded_stats(tmp_path, mocker):
    bundles = generate_bundles(TEST_ROOT / "test_files/144p/")
    db = FileDataBase(tmp_path / "test.json", bundles)

    bundle = db.bundles[0]
    bundle.status = BundleStatus.DONE
    bundle.config = {"output": str(tmp_path)}
    (tmp_path / bundle.name).touch()

    mocker.patch("o3_auto_encode.utils.get_video_frames_fast", return_value=bundle.total_frames)
    probe = {"size": 123, "resolution": "256x144", "bitrate": 456, "fps": 60.0, "codec": "hevc", "frames": 1}
    mocker.patch("o3_auto_encode.utils.probe_video", return_value=probe)

    assert db.validate() is True
    assert bundle.encoded == probe


def test_validate_leaves_encoded_stats_empty_when_unfinished(tmp_path, mocker):
    bundles = generate_bundles(TEST_ROOT / "test_files/144p/")
    db = FileDataBase(tmp_path / "test.json", bundles)

    bundle = db.bundles[0]
    bundle.status = BundleStatus.INTERRUPTED
    probe = mocker.patch("o3_auto_encode.utils.probe_video")

    db.validate()

    assert bundle.encoded is None
    probe.assert_not_called()



