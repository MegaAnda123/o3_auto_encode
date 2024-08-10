"""Class and functions related to file management."""

import os
import re
import subprocess
from pathlib import Path

from dateutil import parser as dateparser
from enums import BundleStatus
from tqdm import tqdm

from o3_auto_encode import utils


class Clip:
    """Class for storing information related to individual video clips.

    Attributes:
        name: Name of the clip (includes file type suffix).
        duration: Clip duration as string, format: `hh:mm:ss.ms`.
        path: Path to the clip file as Path.
        creation_time: Creation time from video file metadata, example format: `2024-05-16T15:21:44.000000Z`.
        creation_time_unix: Creation time from video file metadata as unix timestamp.
        duration_s: Clip duration as float in seconds.
        delta: Time difference between two clips. Used and added by `generate_bundles` function.
        frames: Number of frames in clip.

    """

    name: str
    duration: str
    path: Path
    creation_time: str
    creation_time_unix: float
    duration_s: float
    delta: float
    frames: int

    def __init__(self, path: Path | str):
        # TODO better error handling here.
        self.path = Path(path)
        process = subprocess.run([utils.get_ffprobe_path(), str(path)], capture_output=True)
        ffprobe_string = process.stderr.decode("utf8")
        self.creation_time = re.search(r"\s*creation_time\s*:\s([\w\-:.]*)", ffprobe_string).group(1)
        self.duration = re.search(r"\s*Duration\s*:\s([\w\-:.]*)", ffprobe_string).group(1)
        self.frames = utils.get_video_frames(self.path)

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def creation_time_unix(self) -> float:
        return dateparser.parse(self.creation_time).timestamp()

    @property
    def duration_s(self) -> float:
        h, m, s = self.duration.split(":")
        return float(h) * 3600 + float(m) * 60 + float(s)

    def __dict__(self):
        return {
            "name": self.name,
            "duration": self.duration,
            "path": str(self.path.absolute()),
            "creation_time": self.creation_time,
            "creation_time_unix": self.creation_time_unix,
            "duration_s": self.duration_s,
            "delta": self.delta if hasattr(self, "delta") else None,
            "frames": self.frames,
        }


class Bundle:
    """Clip/video bundle class.

    DJI air unit encodes videos on a FAT32 file system.
    This limits file sizes. DJI splits videos into multiple clips if videos are too long (´>3m14s or > ~3.5GB).
    This class stores information about what clips belong to this "bundle"/video.

    Attributes:
        name: Bundle name.
        clips: Clips belonging to this bundle.
        creation_time: Creation time (creation time from first clip).
        status: Bundle status e.g. found, interrupted, processing, done.
        config: Config used when processing (added when processing is done) #TODO not yet used

    """

    name: str
    clips: list[Clip]
    creation_time: str
    status: BundleStatus
    config: str

    def __init__(self, clips: list[Clip]):
        # Sort clips by creation time (likely unnecessary, all usages provide pre-sorted clips).
        self.clips = [clip for clip in sorted(clips, key=lambda x: x.creation_time_unix)]
        # TODO make name range of clips e.g. clip[0].name to clip[-1].name ?
        self.name = f"{self.clips[0].path.stem}_{self.creation_time.split('T')[0]}.mp4"

    @property
    def creation_time(self) -> str:
        return self.clips[0].creation_time


def generate_bundles(path: Path | str, max_delta: float = 3.0) -> list[Bundle]:
    """Generates list of bundles from path to folder containing air unit clips.

    Args:
        path: Path to folder containing air unit clips.
        max_delta: Max delta in seconds, used to determine what clip belongs to this bundle.

    Returns:
        List of bundle objects.

    """
    path = Path(path)
    clips = []
    for file in tqdm(_get_files(path)):
        clips.append(Clip(file))

    sorted_clips = [clip for clip in sorted(clips, key=lambda x: x.creation_time_unix)]

    temp = []
    bundles = []
    for clip in _add_delta(sorted_clips):
        if clip.delta > max_delta:
            bundles.append(Bundle(temp))
            temp = []
        temp.append(clip)
    bundles.append(Bundle(temp))

    return bundles


def _get_files(folder_path: str | Path) -> list[Path]:
    # TODO only get files encoded by "DJI DEFAULT ENCODING" or similar.
    folder_path = Path(folder_path)

    result = []
    for file in os.listdir(folder_path):
        result.append(Path(os.path.join(folder_path, file)))

    return result


def _add_delta(clips: list[Clip]) -> list[Clip]:
    t1 = clips[0].creation_time_unix
    for clip in clips:
        t2 = clip.creation_time_unix
        d = clip.duration_s
        clip.delta = t2 - t1
        t1 = t2 + d
    return clips
