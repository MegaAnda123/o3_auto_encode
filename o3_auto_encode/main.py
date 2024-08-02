import os
from pathlib import Path

from args_parser import pars_args, LaunchArguments
# from tbd import write_video_db, get_video_bundles, encode_bundles
from o3_auto_encode.file_manager import generate_bundles
from o3_auto_encode.encoder import encode_bundle
from o3_auto_encode.ffmpeg_settings import FFMPEGSettings


def run(launch_args: LaunchArguments) -> None:
    print(launch_args)
    bundles = generate_bundles(launch_args.input_folder)

    for bundle in bundles:
        ffmpeg_settings = FFMPEGSettings("", Path(launch_args.output_folder) / bundle.name)
        ffmpeg_settings.crf = launch_args.crf_quality
        ffmpeg_settings.preset = launch_args.preset

        encode_bundle(bundle, ffmpeg_settings)


if __name__ == '__main__':
    args = pars_args()
    print(args)
    print(os.getcwd())
    run(args)
