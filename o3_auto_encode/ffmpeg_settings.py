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

    def generate_args(self, output_file_name: str) -> list[str]:
        """Generate FFMPEG command line args for running current configuration stored in FFMPEGSettings object.

        Args:
            output_file_name: Output file name.

        Returns:
            List of command line args for running current configuration stored in FFMPEGSettings object.

        """
        if not self.concatenation:
            raise NotImplementedError

        if self.codec in [Codec.H264_NVENC, Codec.H265_NVENC, Codec.AV1_NVENC]:
            return self._generate_gpu_args(output_file_name)
        else:
            return self._generate_cpu_args(output_file_name)

    def _generate_cpu_args(self, output_file_name: str) -> list[str]:
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
            str(Path(self.output / output_file_name).absolute()),
            "-y",
        ]

    def _generate_gpu_args(self, output_file_name: str) -> list[str]:
        # Map EncodePreset to NVENC numeric presets (p1..p7). Default to p7 for slower presets.
        preset_map = {
            EncodePreset.ULTRAFAST: "p1",
            EncodePreset.SUPERFAST: "p2",
            EncodePreset.VERYFAST: "p3",
            EncodePreset.FASTER: "p4",
            EncodePreset.FAST: "p5",
            EncodePreset.MEDIUM: "p5",
            EncodePreset.SLOW: "p6",
            EncodePreset.SLOWER: "p7",
            EncodePreset.VERYSLOW: "p7",
            EncodePreset.PLACEBO: "p7",
        }
        preset_str = preset_map.get(self.preset, "p7")

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
            "-preset",
            preset_str,
            "-cq",
            str(self.crf),
            "-spatial-aq",
            "1",
            "-aq-strength",
            "15",
            "-pix_fmt",
            "p010le",
            str(Path(self.output / output_file_name).absolute()),
            "-y",
        ]

    def summary(self) -> dict[str, str]:
        """Return a concise, stable summary string of the active encoding settings."""
        result = {}
        for k, v in self.__dict__.items():
            result[k] = str(v)
        full_command = " ".join(self.generate_args(str(self.output)))
        result["command"] = full_command
        return result
