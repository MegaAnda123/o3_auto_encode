import os
import platform
import subprocess
from pathlib import Path

from file_manager import Bundle

from o3_auto_encode import logger


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
    """Get frame count from video.

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
            "-count_packets",
            "-show_entries",
            "stream=nb_read_packets",
            "-of",
            "csv=p=0",
            str(path),
        ],
        stdout=subprocess.PIPE,
        text=True,
    )

    return int(process.stdout.strip())


def clean_up_interrupted_video(bundle: Bundle, out_path: Path) -> None:
    """Remove interrupted video based on path in bundle.

    Args:
        bundle: Interrupted video bundle.
        out_path: Target output path for encoding.

    """
    logger.warning(f"Found interrupted video, deleting unfinished video '{bundle.name}'.")

    if (path := Path(out_path / bundle.name)).is_file():
        logger.info(f"Removing '{path.absolute()}'.")
        os.remove(path)
