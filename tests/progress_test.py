import json
import time
from pathlib import Path

from o3_auto_encode import progress
from o3_auto_encode.encoder import _build_payload
from o3_auto_encode.file_manager import Bundle, Clip

TEST_ROOT = Path(__file__).parent


def _bundle() -> Bundle:
    clip = Clip("DJI_0237.MP4", "2024-05-16T15:21:44.000000Z", "00:03:14.73", 100)
    return Bundle([clip])


def test_progress_path_is_next_to_db(tmp_path):
    assert progress.progress_path_for(tmp_path / "out" / ".meta.json") == tmp_path / "out" / "progress.json"


def test_write_and_read_progress(tmp_path):
    path = tmp_path / "progress.json"

    progress.write_progress(path, {"bundle": "a.mp4", "state": "encoding", "frame": 5})
    result = progress.read_progress(path)

    assert result["bundle"] == "a.mp4"
    assert result["frame"] == 5
    assert result["stale"] is False
    assert result["updated_at"] > 0
    assert not (tmp_path / "progress.tmp").exists()


def test_clear_progress_marks_idle(tmp_path):
    path = tmp_path / "progress.json"

    progress.write_progress(path, {"bundle": "a.mp4", "state": "encoding"})
    progress.clear_progress(path)

    assert progress.read_progress(path)["state"] == "idle"
    assert progress.read_progress(path)["bundle"] is None


def test_read_progress_missing_or_corrupt(tmp_path):
    assert progress.read_progress(tmp_path / "nope.json") is None

    corrupt = tmp_path / "progress.json"
    corrupt.write_text("{not json")
    assert progress.read_progress(corrupt) is None


def test_read_progress_flags_stale(tmp_path):
    path = tmp_path / "progress.json"
    path.write_text(json.dumps({"bundle": "a.mp4", "updated_at": time.time() - progress.STALE_AFTER_S - 1}))

    assert progress.read_progress(path)["stale"] is True


def test_build_payload_from_ffmpeg_line():
    line = "frame=   50 fps= 25.0 q=28.0 size=    1024kB time=00:00:02.00 bitrate=4096.0kbits/s speed=1.25x    \r"

    payload = _build_payload(_bundle(), 50, 100, line)

    assert payload["state"] == "encoding"
    assert payload["frame"] == 50
    assert payload["total_frames"] == 100
    assert payload["percent"] == 50.0
    assert payload["fps"] == 25.0
    assert payload["speed"] == 1.25
    assert payload["eta_s"] == 2.0


def test_build_payload_without_fps():
    payload = _build_payload(_bundle(), 10, 100, "frame=   10 q=28.0\r")

    assert payload["fps"] is None
    assert payload["eta_s"] is None

