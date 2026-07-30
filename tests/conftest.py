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
            result = re.sub(r"\"config\"\:\s(\{[\w\W]*?\})", '"config": null', result)
        else:
            result = re.sub(r"path\:(.*[\\/])", "path: ABS_PATH ", result)
            expected = re.sub(r"path\:(.*[\\/])", "path: ABS_PATH ", expected)

        result = Helpers.strip_machine_stats(result, Path(expected_path).suffix)
        expected = Helpers.strip_machine_stats(expected, Path(expected_path).suffix)

        assert result == expected

    @staticmethod
    def strip_machine_stats(content: str, suffix: str) -> str:
        """Remove probe based stats (size/resolution/bitrate/fps/codec/encoded) from a serialized database.

        These depend on the local ffprobe build and are asserted separately, so they are excluded
        from the golden file comparison.

        Args:
            content: Serialized database content.
            suffix: File suffix of the database file (`.json`, `.yaml` or `.yml`).

        Returns:
            Content without the probe based stat entries.

        """
        if suffix == ".json":
            # Drop the trailing clip stat block including the preceding comma.
            content = re.sub(r",\n\s*\"size\"\:[\w\W]*?\"codec\"\:\s[^\n]*", "", content)
            content = re.sub(r"^[ \t]*\"encoded\"\:[^\n]*\n", "", content, flags=re.MULTILINE)
        else:
            content = re.sub(
                r"^[ \t]*(size|resolution|bitrate|fps|codec|encoded)\:[^\n]*\n", "", content, flags=re.MULTILINE
            )
        return content


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
