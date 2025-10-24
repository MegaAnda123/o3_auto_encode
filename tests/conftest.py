import os
import re
from pathlib import Path

import pytest
import yaml

TEST_ROOT = Path(__file__).parent


def pytest_addoption(parser):
    parser.addoption("--4k", action="store", default="false", help="run 4k tests")


class Helpers:
    @staticmethod
    def test_db_files(result_path: Path, expected_path: Path) -> None:
        """Test database files json or yaml.

        Substitutes absolute paths in file to make testing on different machines possible.

        Args:
            result_path: Path to result file.
            expected_path: Path to expected file.

        """
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

    @staticmethod
    def get_test_config(tmp_path: Path) -> Path:
        config = {
            "codec": "libx264",
            "preset": "fast",
            "crf": 50,
            "input": str(TEST_ROOT / "test_files/144p"),
            "output": str(tmp_path),
        }

        config_path = tmp_path / "config.yml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)
        return config_path

    @staticmethod
    def get_test_config_4k(tmp_path: Path) -> Path:
        config = {
            "codec": "av1_nvenc",
            "preset": "ultrafast",
            "crf": 50,
            "input": str(TEST_ROOT / "test_files/4k"),
            "output": str(tmp_path),
        }

        config_path = tmp_path / "config.yml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)
        return config_path

def pytest_sessionstart(session):

    if (short := session.config.getvalue("--4k")) is not None:
        os.environ["4k"] = str(short).lower()

@pytest.fixture
def helpers() -> Helpers:
    return Helpers()
