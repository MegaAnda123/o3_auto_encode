from pathlib import Path

from o3_auto_encode import utils
from o3_auto_encode.enums import Codec, EncodePreset


class FFMPEGSettings:

    codec: Codec
    crf: int
    preset: EncodePreset
    concatenation: bool
    input: Path
    output: Path

    def __init__(self, input_: Path | str, output: Path | str):
        self.input = Path(input_)
        self.output = Path(output)
        self.codec = Codec.X265
        self.crf = 30
        self.preset = EncodePreset.SLOWER
        self.concatenation = True

    @classmethod
    def from_json(cls, path: Path):
        # TODO
        raise NotImplementedError

    def generate_args(self) -> list[str]:
        if not self.concatenation:
            raise NotImplementedError

        return [
            utils.get_ffmpeg_path(),
            "-safe",
            "0",
            "-f",
            "concat",
            "-i",
            str(self.input.absolute()),
            "-c:v",
            str(self.codec),
            "-crf",
            str(self.crf),
            "-preset",
            str(self.preset),
            str(self.output.absolute()),
        ]
