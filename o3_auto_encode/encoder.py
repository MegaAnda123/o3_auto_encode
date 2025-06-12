import re
import subprocess
import tempfile
from pathlib import Path

from tqdm import tqdm

from o3_auto_encode.ffmpeg_settings import FFMPEGSettings
from o3_auto_encode.file_manager import Bundle


def encode_bundle(bundle: Bundle, ffmpeg_setting: FFMPEGSettings) -> None:
    list_string = ""
    for clip in bundle.clips:
        list_string += f"file '{clip.path.absolute()}'\n"

    tempfile.gettempdir()
    with tempfile.TemporaryDirectory() as temp_dir:
        tmp_file = Path(temp_dir) / "list.txt"
        with open(tmp_file, "w") as f:
            f.write(list_string)

        ffmpeg_setting.input = tmp_file
        ffmpeg_with_progress(bundle, ffmpeg_setting)


def ffmpeg_with_progress(bundle: Bundle, ffmpeg_setting: FFMPEGSettings) -> None:
    if ffmpeg_setting.output.is_file():
        raise FileExistsError

    process = subprocess.Popen(
        ffmpeg_setting.generate_args(bundle.name), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    total_frames = sum([clip.frames for clip in bundle.clips])
    with tqdm(total=total_frames, desc=f"Encoding: {bundle.name}") as pbar:
        try:
            for line in iter(process.stderr.readline, ""):
                if line.startswith("frame="):
                    try:
                        frame = re.match(r"frame=\s*(\d+)", line).group(1)
                        pbar.n = int(frame)
                        pbar.refresh()
                    except AttributeError:
                        pass
        except (KeyboardInterrupt, SystemExit) as e:
            process.kill()
            raise KeyboardInterrupt() from e
