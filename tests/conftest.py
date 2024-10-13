import re
from pathlib import Path

import pytest
import yaml

TEST_ROOT = Path(__file__).parent


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


@pytest.fixture
def helpers() -> Helpers:
    return Helpers()
