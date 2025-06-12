import argparse
from dataclasses import dataclass


@dataclass
class LaunchArguments:
    config_path: str
    json_path: str


def pars_args() -> LaunchArguments:
    arg_parser = argparse.ArgumentParser(
        description="Tool for encoding separated o3 clips to one video with substantially lower bitrate.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    arg_parser.add_argument(
        "-c",
        "--config",
        type=str,
        default="config.yaml",
        help="File with config data on how the program should behave.",
    )
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
        config_path=args.config,
        json_path=args.json,
    )
