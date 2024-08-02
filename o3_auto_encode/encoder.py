from pathlib import Path

from o3_auto_encode.file_manager import Bundle
import tempfile
import subprocess
from o3_auto_encode.ffmpeg_settings import FFMPEGSettings


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
        subprocess.run(ffmpeg_setting.generate_args())


