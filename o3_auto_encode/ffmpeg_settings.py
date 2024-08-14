"""File for FFMPEGSettings class."""

import json
from pathlib import Path

import yaml

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

    def __init__(self, path: Path | str = None):
        self.input = None
        self.output = None
        self.codec = Codec.X265
        self.crf = 30
        self.preset = EncodePreset.SLOWER
        self.concatenation = True

        if path is None:
            return

        # Initialize from file if path is specified.
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(f"Could not find file `{path.absolute()}`.")

        match path.suffix:
            case ".yaml":
                data = yaml.safe_load(path.open())
            case ".yml":
                data = yaml.safe_load(path.open())
            case ".json":
                data = json.load(path.open())
            case _:
                raise ValueError(f"Unsupported file type `{path.suffix}`.")

        self.input = None if data.get("input") is None else Path(data["input"])
        self.output = None if data.get("output") is None else Path(data["output"])
        self.codec = self.codec if data.get("codec") is None else Codec(data["codec"])
        self.crf = self.crf if data.get("crf") is None else int(data["crf"])
        self.preset = self.preset if data.get("preset") is None else EncodePreset(data["preset"])
        self.concatenation = self.concatenation if data.get("concatenation") is None else data["concatenation"]

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
