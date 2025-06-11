import re
from pathlib import Path

import pytest

from o3_auto_encode.db import FileDataBase
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
def test_db(tmp_path, file_name, expected_file):
    db_path = Path(tmp_path, file_name)
    expected_path = TEST_ROOT / f"test_files/expected/{expected_file}"

    bundles = generate_bundles(TEST_ROOT / "test_files/144p/")
    db = FileDataBase(db_path)
    db.bundles = bundles
    db.write()

    assert_file(db_path, expected_path)


@pytest.mark.parametrize(
    "file_name",
    [
        "db_expected1.json",
        "db_expected2.yaml",
    ],
)
def test_file_initialization(tmp_path, file_name):
    db_path = TEST_ROOT / f"test_files/expected/{file_name}"

    db = FileDataBase(db_path)
    db.init_from_file()

    result_path = Path(tmp_path, file_name)
    db.path = result_path
    db.write()

    assert_file(result_path, db_path)


def assert_file(result_path: Path, expected_path: Path) -> None:
    with open(result_path) as f:
        result = f.read()
    with open(expected_path) as f:
        expected = f.read()

    # Replace absolute paths in expected and result data.
    if Path(expected_path).suffix == ".json":
        result = re.sub(r"\"path\"\: \"(.*[\\/])", "path: ABS_PATH ", result)
        expected = re.sub(r"\"path\"\: \"(.*[\\/])", "path: ABS_PATH ", expected)
    else:
        result = re.sub(r"path\:(.*[\\/])", "path: ABS_PATH ", result)
        expected = re.sub(r"path\:(.*[\\/])", "path: ABS_PATH ", expected)

    assert result == expected
