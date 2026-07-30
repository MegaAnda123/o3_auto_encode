import re
import subprocess
import tempfile
import time
from pathlib import Path

from tqdm import tqdm

from o3_auto_encode import logger, progress
from o3_auto_encode.ffmpeg_settings import FFMPEGSettings
from o3_auto_encode.file_manager import Bundle

# Minimum time between heartbeat writes.
_PROGRESS_INTERVAL_S = 0.5


def encode_bundle(bundle: Bundle, ffmpeg_setting: FFMPEGSettings, progress_path: Path | str | None = None) -> None:
    list_string = ""
    for clip in bundle.clips:
        list_string += f"file '{clip.path.absolute()}'\n"

    tempfile.gettempdir()
    with tempfile.TemporaryDirectory() as temp_dir:
        tmp_file = Path(temp_dir) / "list.txt"
        with open(tmp_file, "w") as f:
            f.write(list_string)

        ffmpeg_setting.input = tmp_file
        ffmpeg_with_progress(bundle, ffmpeg_setting, progress_path)


def ffmpeg_with_progress(
    bundle: Bundle, ffmpeg_setting: FFMPEGSettings, progress_path: Path | str | None = None
) -> None:
    if ffmpeg_setting.output.is_file():
        raise FileExistsError

    process = subprocess.Popen(
        ffmpeg_setting.generate_args(bundle.name, bundle.creation_time),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    total_frames = bundle.total_frames
    last_write = 0.0
    with tqdm(total=total_frames, desc=f"Encoding: {bundle.name}", unit="frames") as pbar:
        try:
            for line in iter(process.stderr.readline, ""):
                logger.debug(line)
                if not line.startswith("frame="):
                    continue
                try:
                    frame = int(re.match(r"frame=\s*(\d+)", line).group(1))
                except AttributeError:
                    continue

                pbar.n = frame
                pbar.refresh()

                if progress_path is None:
                    continue
                now = time.monotonic()
                if now - last_write < _PROGRESS_INTERVAL_S and frame < total_frames:
                    continue
                last_write = now
                progress.write_progress(progress_path, _build_payload(bundle, frame, total_frames, line))
        except (KeyboardInterrupt, SystemExit) as e:
            process.kill()
            raise KeyboardInterrupt() from e


def _build_payload(bundle: Bundle, frame: int, total_frames: int, line: str) -> dict:
    """Build the heartbeat payload from an ffmpeg progress line."""
    fps = _search_float(r"fps=\s*([\d.]+)", line)
    speed = _search_float(r"speed=\s*([\d.]+)x", line)

    eta_s = None
    if fps:
        eta_s = round(max(total_frames - frame, 0) / fps, 1)

    return {
        "bundle": bundle.name,
        "state": "encoding",
        "frame": frame,
        "total_frames": total_frames,
        "percent": round(frame / total_frames * 100, 2) if total_frames else None,
        "fps": fps,
        "speed": speed,
        "eta_s": eta_s,
    }


def _search_float(pattern: str, line: str) -> float | None:
    match = re.search(pattern, line)
    if match is None:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None

