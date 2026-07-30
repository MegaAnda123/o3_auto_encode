import json
import os
from pathlib import Path, PurePath

import pytest
import yaml

TEST_ROOT = Path(__file__).parent


def pytest_addoption(parser):
    parser.addoption("--4k", action="store", default="false", help="run 4k tests")


class Helpers:
    # Probe based clip stats depend on the local ffprobe build, they are asserted separately.
    CLIP_STAT_KEYS = ("size", "resolution", "bitrate", "fps", "codec")

    @staticmethod
    def test_db_files(result_path: Path, expected_path: Path) -> None:
        """Test database files json or yaml.

        Compares parsed content instead of raw text so formatting and machine specific values
        (absolute paths, probe stats, encode config) do not cause false failures.

        Args:
            result_path: Path to result file.
            expected_path: Path to expected file.

        """
        result = Helpers.normalize_db(Helpers.load_db(result_path))
        expected = Helpers.normalize_db(Helpers.load_db(expected_path))

        assert result == expected

    @staticmethod
    def load_db(path: Path) -> list:
        """Load a json/yaml database file."""
        path = Path(path)
        with open(path) as f:
            if path.suffix == ".json":
                return json.load(f)
            return yaml.safe_load(f)

    @staticmethod
    def normalize_db(bundles: list) -> list:
        """Strip machine specific values so two databases can be compared."""
        normalized = []
        for bundle in bundles or []:
            bundle = dict(bundle)
            # Encode config and encoded output stats depend on the machine/run.
            bundle["config"] = None
            bundle.pop("encoded", None)
            bundle["clips"] = [Helpers._normalize_clip(clip) for clip in bundle.get("clips", [])]
            normalized.append(bundle)
        return normalized

    @staticmethod
    def _normalize_clip(clip: dict) -> dict:
        clip = dict(clip)
        for key in Helpers.CLIP_STAT_KEYS:
            clip.pop(key, None)
        if clip.get("path"):
            # Absolute paths differ between machines.
            clip["path"] = PurePath(str(clip["path"]).replace("\\", "/")).name
        return clip

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
