"""File for FFMPEGSettings class."""

import json
from pathlib import Path

from o3_auto_encode import utils
from o3_auto_encode.enums import Codec, EncodePreset


class FFMPEGSettings:
    """Class for storing FFMPEG configuration and generating easy to use list of arguments.

    Attributes:
        codec: Codec to use when encoding.
        crf: Constant rate factor to use when encoding.
        preset: Encode preset to use when encoding.
        concatenation: If file concatenation should be done (option might get removed).
        input: Path to txt file containing files to concatenate (only concatenation implemented atm).
        output: Output path.

    """

    codec: Codec
    crf: int
    preset: EncodePreset
    concatenation: bool
    input: Path | None
    output: Path | None

    def __init__(self):
        self.input = None
        self.output = None
        self.codec = Codec.X265
        self.crf = 30
        self.preset = EncodePreset.SLOWER
        self.concatenation = True

    @classmethod
    def from_json(cls, path: Path):
        """Load FFMPEG settings from json file.

        Args:
            path: Path to json file.

        Returns:
            FFMPEG settings object.

        """
        # TODO move to __init__ ??
        settings = cls()
        j = json.load(path.open())
        settings.input = None if j.get("input") is None else Path(j["input"])
        settings.output = None if j.get("output") is None else Path(j["output"])
        settings.codec = settings.codec if j.get("codec") is None else Codec(j["codec"])
        settings.crf = settings.crf if j.get("crf") is None else int(j["crf"])
        settings.preset = settings.preset if j.get("preset") is None else EncodePreset(j["preset"])
        settings.concatenation = settings.concatenation if j.get("concatenation") is None else j["concatenation"]

        return settings

    def generate_args(self) -> list[str]:
        """Generate FFMPEG command line args for running current configuration stored in FFMPEGSettings object.

        Returns:
            List of command line args for running current configuration stored in FFMPEGSettings object.

        """
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
