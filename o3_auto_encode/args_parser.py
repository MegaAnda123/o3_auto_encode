import argparse
from dataclasses import dataclass


@dataclass
class LaunchArguments:
    input_folder: str
    output_folder: str
    json_path: str
    crf_quality: int
    preset: str


def pars_args() -> LaunchArguments:
    arg_parser = argparse.ArgumentParser(
        description="Tool for encoding separated o3 clips to one video with substantially lower bitrate.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    arg_parser.add_argument("input_folder", type=str, nargs="?", help="Target folder with clips to encode.")
    arg_parser.add_argument("output_folder", type=str, nargs="?", help="Target folder where output will be stored.")
    arg_parser.add_argument(
        "-q",
        "--crf",
        type=int,
        default=30,
        help="The CRF value can be from 0–63. "
        "Lower values mean better quality and greater file size. 0 means lossless. "
        "For o3 encoded to h264 CRF 30 (the default) seems to be visually lossless (encoding to x265 @slower).",
    )
    arg_parser.add_argument("-p", "--preset", type=str, default="slower", help="Encoding preset (fast, slow, etc).")
    arg_parser.add_argument("-c", "--config", type=str, )
    # TODO deprecate (use couchDB)
    arg_parser.add_argument(
        "-j",
        "--json",
        type=str,
        default=f"/out/.meta.json",
        help="Where to store json file containing progress and metadata.",
    )

    args = arg_parser.parse_args()

    return LaunchArguments(
        input_folder=args.input_folder,
        output_folder=args.output_folder,
        json_path=args.json,
        crf_quality=args.crf,
        preset=args.preset,
    )
