import os
from pathlib import Path
import subprocess
import re
from dateutil import parser
from tqdm import tqdm
from args_parser import pars_args


def get_sec(time_str: str) -> float:
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
    result["creation_time_utc"] = parser.parse(result["creation_time"]).timestamp()
    result["duration_s"] = get_sec(result["duration"])
    return result


def get_video_info(path: Path) -> dict:
    ffprobe_path = "../ffprobe.exe"
    process = subprocess.run([ffprobe_path, str(path)], capture_output=True)
    return parse_ffprobe_output(process.stderr.decode("utf8"))


def add_delta(info: list[dict]) -> list[dict]:
    t1 = info[0]["creation_time_utc"]
    for f in info:
        t2 = f["creation_time_utc"]
        d = f["duration_s"]
        f["delta"] = t2-t1
        t1 = t2+d
    return info


def get_video_bundles(path: str | Path, max_delta: float = 3.0):
    info = []
    for file in tqdm(get_files(path)):
        video_info = get_video_info(file)
        video_info["file"] = file
        info.append(video_info)

    sorted_info = [x for x in sorted(info, key=lambda x: x["creation_time_utc"])]

    bundles = []
    bundle = {}
    for v in add_delta(sorted_info):
        if v["delta"] > max_delta:
            bundles.append(bundle)
            bundle = {}
        bundle[v["file"].name] = v
    bundles.append(bundle)

    return bundles


def encode_bundles(bundle_info: list[dict], destination: Path | str, crf: int = 30, preset: str = "slower") -> None:
    path = Path(destination)

    for bundle in tqdm(bundle_info, desc="Encoding..."):
        list_string = ""
        for video in bundle.values():
            list_string += f"file '{video['file']}'\n"
        with open("../temp/list.txt", "w") as f:
            f.write(list_string)
        temp = list(bundle.values())[0]
        name = (temp["file"].stem + "_" + temp["creation_time"]).split("T")[0]
        if (name + ".mp4") in os.listdir(path):
            print(f"Skipping '{name}'.")
        else:
            subprocess.run([
                "..\\ffmpeg.exe",
                "-safe",
                "0",
                "-f",
                "concat",
                "-i",
                "..\\temp\\list.txt",
                "-c:v",
                "libx265",
                "-crf",
                str(crf),
                "-preset",
                preset,
                f"{path}\\{name}.mp4"
                ],
                stdout=subprocess.PIPE
            )


if __name__ == '__main__':
    args = pars_args()
    print(args)
    videos = get_video_bundles(args.input_folder)
    encode_bundles(videos, args.output_folder, args.crf_quality, args.preset)
