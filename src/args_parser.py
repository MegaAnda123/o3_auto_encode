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
        help="Encoding (crf) quality lower better (larger file) higher worse (smaller file)."
    )
    arg_parser.add_argument(
        "-p",
        "--preset",
        type=str,
        default="slower",
        help="Encoding preset (fast, slow, etc)."
    )
    arg_parser.add_argument(
        "-j",
        "--json",
        type=str,
        default=f"/out/.meta.json",
        help="Where to store json file containing progress and metadata."
    )

    args = arg_parser.parse_args()

    return LaunchArguments(
        input_folder=args.input_folder,
        output_folder=args.output_folder,
        json_path=args.json,
        crf_quality=args.crf,
        preset=args.preset,
    )
