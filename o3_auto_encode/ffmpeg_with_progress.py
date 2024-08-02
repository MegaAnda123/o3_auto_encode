import re
import subprocess

import utils

import tqdm


def _get_total_frames(bundle) -> int:
    frames = 0
    for k, v in bundle.items():
        if isinstance(v, dict):
            frames += utils.get_video_frames(v["abs_path"])

    return frames


def ffmpeg_with_progress(args_, bundle, path) -> None:
    """ TODO

    Args:
        ffmpeg_path:
        args_:
        bundle:
        path:

    Returns:

    """

    total_frames = _get_total_frames(bundle)

    # TODO use ffmpeg config object
    process = subprocess.Popen([
        utils.get_ffmpeg_path(),
        "-safe",
        "0",
        "-f",
        "concat",
        "-i",
        "list.txt",
        "-c:v",
        "libx264",
        # "h264_nvenc",
        "-crf",
        str(args_.crf_quality),
        "-preset",
        args_.preset,
        f"{path}/{bundle['name']}.mp4"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    with tqdm.tqdm(total=total_frames, desc=f"Encoding: {bundle['name']}") as pbar:
        for line in iter(process.stderr.readline, ''):
            if line.startswith("frame="):
                try:
                    frame = re.match(r"frame=\s*(\d+)", line).group(1)
                    pbar.n = int(frame)
                    pbar.refresh()
                except AttributeError:
                    pass
