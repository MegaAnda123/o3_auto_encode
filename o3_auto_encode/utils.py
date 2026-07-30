import json
import platform
import subprocess
from pathlib import Path
from typing import Any


def _get_project_root() -> Path:
    return Path(__file__).parent.parent


def get_ffmpeg_path() -> str:
    """OS independent ffmpeg 'path'.

    Returns:
        Path to ffmpeg executable.

    """
    exe_path = str(_get_project_root() / "ffmpeg.exe")
    return exe_path if platform.system() == "Windows" else "ffmpeg"


def get_ffprobe_path() -> str:
    """OS independent ffprobe 'path'.

    Returns:
        Path to ffprobe executable.

    """
    exe_path = str(_get_project_root() / "ffprobe.exe")
    return exe_path if platform.system() == "Windows" else "ffprobe"


def get_video_frames(video_path: Path | str) -> int:
    """Get frame count from video file header.

    Args:
        video_path: Video path.

    Returns:
        Frame count.

    """
    path = Path(video_path)
    ffprobe = get_ffprobe_path()

    process = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=nb_frames",
            "-of",
            "csv=p=0",
            str(path),
        ],
        stdout=subprocess.PIPE,
        text=True,
    )
    return int(process.stdout.strip())


def get_video_frames_fast(video_path: Path | str) -> int:
    """Get frame count from video file header.

    Args:
        video_path: Video path.

    Returns:
        Frame count.

    """
    path = Path(video_path)
    ffprobe = get_ffprobe_path()

    process = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=nb_frames",
            "-of",
            "csv=p=0",
            str(path),
        ],
        stdout=subprocess.PIPE,
        text=True,
    )
    return int(process.stdout.strip())


def probe_video(video_path: Path | str) -> dict[str, Any]:
    """Probe a video file once and return the stats used by the frontend.

    Args:
        video_path: Video path.

    Returns:
        Dict with `size`, `width`, `height`, `resolution`, `bitrate`, `fps`, `codec` and `frames`.
        Values that could not be determined are `None`.

    """
    path = Path(video_path)

    result: dict[str, Any] = {
        "size": None,
        "width": None,
        "height": None,
        "resolution": None,
        "bitrate": None,
        "fps": None,
        "codec": None,
        "frames": None,
    }

    if not path.is_file():
        return result

    result["size"] = path.stat().st_size

    process = subprocess.run(
        [
            get_ffprobe_path(),
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=nb_frames,width,height,bit_rate,avg_frame_rate,codec_name:format=bit_rate,duration,size",
            "-of",
            "json",
            str(path),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if process.returncode != 0:
        return result

    try:
        data = json.loads(process.stdout)
    except json.JSONDecodeError:
        return result

    streams = data.get("streams") or [{}]
    stream = streams[0]
    fmt = data.get("format") or {}

    result["width"] = _to_int(stream.get("width"))
    result["height"] = _to_int(stream.get("height"))
    if result["width"] and result["height"]:
        result["resolution"] = f"{result['width']}x{result['height']}"

    result["codec"] = stream.get("codec_name")
    result["frames"] = _to_int(stream.get("nb_frames"))
    result["fps"] = _parse_frame_rate(stream.get("avg_frame_rate"))

    bitrate = _to_int(stream.get("bit_rate")) or _to_int(fmt.get("bit_rate"))
    if bitrate is None and result["size"] is not None:
        duration = _to_float(fmt.get("duration"))
        if duration:
            bitrate = int(result["size"] * 8 / duration)
    result["bitrate"] = bitrate

    return result


def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_frame_rate(value: Any) -> float | None:
    """Convert an ffprobe frame rate fraction (e.g. `60/1`) to float."""
    if not isinstance(value, str) or "/" not in value:
        return _to_float(value)
    numerator, denominator = value.split("/", 1)
    num = _to_float(numerator)
    den = _to_float(denominator)
    if not num or not den:
        return None
    return round(num / den, 3)
