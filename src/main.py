import json
import os
from pathlib import Path
import subprocess
import re
import time
from dateutil import parser
from tqdm import tqdm
from args_parser import pars_args, LaunchArguments
from ffmpeg_with_progress import ffmpeg_with_progress
import utils

FFMPEG = utils.get_ffmpeg_path()
FFPROBE = utils.get_ffprobe_path()


def is_transferring(path: str, min_delta: float = 1.0) -> bool:
    """Check if folder has an ongoing file transfer,
    if any file in the given folder has a modification time below `min_delta`, True is returned.

    Args:
        path: Folder path to check.
        min_delta: Time difference to trigger boolean.

    Returns:
        If given folder has an active file transfer on any file in the folder.

    """
    # TODO WIP
    files = os.listdir(path)
    print(files)

    for file in files:
        delta = time.time() - os.path.getmtime(os.path.join(path, file))
        if delta < min_delta:
            return True
    return False


def write_video_db(videos: list[dict], path: Path | str):
    path = Path(path)
    v_copy = videos.copy()
    for video in v_copy:
        for v in video.values():
            if isinstance(v, dict):
                v["file"] = str(v["file"])

    with open(path, "w") as f:
        f.write(json.dumps(v_copy, indent=4))


def get_sec(time_str: str) -> float:
    """Convert time string to seconds (format hh:mm:ss.ms).

    Args:
        time_str: Time string to convert.

    Returns:
        Seconds as float.

    """
    h, m, s = time_str.split(":")
    return float(h) * 3600 + float(m) * 60 + float(s)


def get_files(folder_path: str | Path) -> list[Path]:
    if isinstance(folder_path, str):
        folder_path = Path(folder_path)

    result = []
    for file in os.listdir(folder_path):
        result.append(Path(os.path.join(folder_path, file)))

    return result


def parse_ffprobe_output(ffprobe_string: str) -> dict:
    result = {}

    result["creation_time"] = re.search(r"\s*creation_time\s*:\s([\w\-:.]*)", ffprobe_string).group(1)
    result["duration"] = re.search(r"\s*Duration\s*:\s([\w\-:.]*)", ffprobe_string).group(1)
    result["creation_time_unix"] = parser.parse(result["creation_time"]).timestamp()
    result["duration_s"] = get_sec(result["duration"])
    return result


def get_video_info(path: Path) -> dict:
    process = subprocess.run([FFPROBE, str(path)], capture_output=True)
    return parse_ffprobe_output(process.stderr.decode("utf8"))


def add_delta(info: list[dict]) -> list[dict]:
    t1 = info[0]["creation_time_unix"]
    for f in info:
        t2 = f["creation_time_unix"]
        d = f["duration_s"]
        f["delta"] = t2-t1
        t1 = t2+d
    return info


def get_video_bundles(path: str | Path, max_delta: float = 3.0):
    def add_meta():
        temp = list(bundle.values())[0]
        bundle["name"] = (temp["file"].stem + "_" + temp["creation_time"]).split("T")[0]
        bundle["status"] = "found"

    info = []
    for file in tqdm(get_files(path)):
        video_info = get_video_info(file)
        video_info["file"] = file
        video_info["abs_path"] = str(file.absolute())
        info.append(video_info)

    sorted_info = [x for x in sorted(info, key=lambda x: x["creation_time_unix"])]

    bundles = []
    bundle = {}
    for v in add_delta(sorted_info):
        if v["delta"] > max_delta:
            add_meta()
            bundles.append(bundle)
            bundle = {}
        bundle[v["file"].name] = v
    add_meta()
    bundles.append(bundle)

    return bundles


def encode_bundles(bundle_info: list[dict], args_: LaunchArguments) -> None:
    path = Path(args_.output_folder)
    # TODO make bundle data class
    for bundle in tqdm(bundle_info, desc="Encoding..."):
        list_string = ""
        for video in bundle.values():
            if isinstance(video, dict):
                list_string += f"file '{video['file']}'\n"
        with open("list.txt", "w") as f:
            f.write(list_string)

        if (bundle["name"] + ".mp4") in os.listdir(path):
            print(f"Skipping '{bundle['name']}'.")
            bundle["status"] = "done"
            write_video_db(bundle_info, args_.json_path)
        else:
            bundle["status"] = "interrupted"
            write_video_db(bundle_info, args_.json_path)
            ffmpeg_with_progress(FFMPEG, args_, bundle, path)
            # subprocess.run([
            #     "ffmpeg",
            #     "-safe",
            #     "0",
            #     "-f",
            #     "concat",
            #     "-i",
            #     "list.txt",
            #     "-c:v",
            #     "libx265",
            #     "-crf",
            #     str(args_.crf_quality),
            #     "-preset",
            #     args_.preset,
            #     f"{path}/{bundle['name']}.mp4"
            #     ],
            #     stdout=subprocess.PIPE
            # )
            bundle["status"] = "done"
            bundle["config"] = str(args_)
            write_video_db(bundle_info, args_.json_path)


if __name__ == '__main__':
    args = pars_args()
    print(args)
    print(os.getcwd())
    videos_ = get_video_bundles(args.input_folder)
    write_video_db(videos_, args.json_path)
    encode_bundles(videos_, args)


def test_entry(args_: LaunchArguments) -> None:
    print(args_)
    videos__ = get_video_bundles(args_.input_folder)
    write_video_db(videos__, args_.json_path)
    encode_bundles(videos__, args_)

