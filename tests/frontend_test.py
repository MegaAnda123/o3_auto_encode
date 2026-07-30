import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from frontend.app import app
from o3_auto_encode import progress

TEST_ROOT = Path(__file__).parent


def _clip(name: str, size: int) -> dict:
    return {
        "name": name,
        "duration": "00:01:00.00",
        "path": str(TEST_ROOT / "test_files/144p" / name),
        "creation_time": "2024-05-16T15:21:44.000000Z",
        "creation_time_unix": 1715872904.0,
        "duration_s": 60.0,
        "delta": 0.0,
        "frames": 100,
        "size": size,
        "resolution": "256x144",
        "bitrate": 1_000_000,
        "fps": 60.0,
        "codec": "h264",
    }


def _write_db(tmp_path: Path, bundles: list[dict]) -> Path:
    db_path = tmp_path / ".meta.json"
    db_path.write_text(json.dumps(bundles))
    return db_path


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("O3_DB_PATH", str(tmp_path / ".meta.json"))
    monkeypatch.setenv("O3_CONFIG_PATH", str(TEST_ROOT / "test_files/ffmpeg_configs/test_config_1.yaml"))
    return TestClient(app)


def test_health(client, tmp_path):
    result = client.get("/api/health").json()

    assert result["status"] == "ok"
    assert result["db_exists"] is False


def test_bundles_empty_without_db(client):
    assert client.get("/api/bundles").json() == {"bundles": []}


def test_bundle_source_stats(client, tmp_path):
    _write_db(
        tmp_path,
        [
            {
                "name": "DJI_0237_2024-05-16.mp4",
                "status": "found",
                "config": None,
                "clips": [_clip("DJI_0237.MP4", 1000), _clip("DJI_0238.MP4", 1000)],
            }
        ],
    )

    bundle = client.get("/api/bundles").json()["bundles"][0]

    assert bundle["clip_count"] == 2
    assert bundle["total_frames"] == 200
    assert bundle["total_size"] == 2000
    assert bundle["resolution"] == "256x144"
    assert bundle["clips"][0]["bitrate"] == 1_000_000


def test_unfinished_bundle_has_no_encoded_stats_or_settings(client, tmp_path):
    for status in ["found", "processing", "interrupted"]:
        _write_db(
            tmp_path,
            [
                {
                    "name": "DJI_0237_2024-05-16.mp4",
                    "status": status,
                    "config": {"output": str(tmp_path), "codec": "libx265"},
                    "encoded": {"size": 500},
                    "clips": [_clip("DJI_0237.MP4", 1000)],
                }
            ],
        )

        bundle = client.get("/api/bundles").json()["bundles"][0]

        assert bundle["encoded"] is None, status
        assert bundle["settings"] is None, status


def test_finished_bundle_exposes_savings_and_settings(client, tmp_path):
    _write_db(
        tmp_path,
        [
            {
                "name": "DJI_0237_2024-05-16.mp4",
                "status": "verified",
                "config": {
                    "output": str(tmp_path),
                    "codec": "libx265",
                    "preset": "slower",
                    "crf": "30",
                    "command": "ffmpeg ...",
                },
                "encoded": {"size": 250, "resolution": "256x144", "bitrate": 500, "fps": 60.0, "codec": "hevc"},
                "clips": [_clip("DJI_0237.MP4", 1000)],
            }
        ],
    )

    bundle = client.get("/api/bundles/DJI_0237_2024-05-16.mp4").json()

    assert bundle["encoded"]["size"] == 250
    assert bundle["encoded"]["savings_pct"] == 75.0
    assert bundle["encoded"]["codec"] == "hevc"
    assert bundle["settings"]["preset"] == "slower"
    assert bundle["settings"]["command"] == "ffmpeg ..."


def test_unknown_bundle_returns_404(client, tmp_path):
    _write_db(tmp_path, [])

    assert client.get("/api/bundles/nope.mp4").status_code == 404


def test_progress_endpoint(client, tmp_path):
    assert client.get("/api/progress").json()["state"] == "unknown"

    progress.write_progress(progress.progress_path_for(tmp_path / ".meta.json"), {"bundle": "a.mp4", "frame": 3})
    result = client.get("/api/progress").json()

    assert result["bundle"] == "a.mp4"
    assert result["stale"] is False


def test_clip_media_supports_range(client, tmp_path):
    _write_db(
        tmp_path,
        [
            {
                "name": "DJI_0237_2024-05-16.mp4",
                "status": "found",
                "config": None,
                "clips": [_clip("DJI_0237.MP4", 1000)],
            }
        ],
    )

    url = "/api/media/clip/DJI_0237_2024-05-16.mp4/DJI_0237.MP4"

    full = client.get(url)
    assert full.status_code == 200
    assert full.headers["accept-ranges"] == "bytes"

    partial = client.get(url, headers={"Range": "bytes=0-9"})
    assert partial.status_code == 206
    assert len(partial.content) == 10


def test_output_media_blocked_until_encoded(client, tmp_path):
    _write_db(
        tmp_path,
        [
            {
                "name": "DJI_0237_2024-05-16.mp4",
                "status": "processing",
                "config": {"output": str(tmp_path)},
                "clips": [_clip("DJI_0237.MP4", 1000)],
            }
        ],
    )

    assert client.get("/api/media/output/DJI_0237_2024-05-16.mp4").status_code == 409


def test_index_is_served(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "o3 auto encode" in response.text
