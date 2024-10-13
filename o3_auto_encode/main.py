from pathlib import Path

from db import FileDataBase
from enums import BundleStatus

from o3_auto_encode import logger
from o3_auto_encode.args_parser import LaunchArguments, pars_args
from o3_auto_encode.encoder import encode_bundle
from o3_auto_encode.ffmpeg_settings import FFMPEGSettings
from o3_auto_encode.file_manager import generate_bundles


def run(launch_args: LaunchArguments) -> None:
    logger.debug(str(launch_args))
    db = FileDataBase(launch_args.json_path, generate_bundles(launch_args.input_folder))

    for bundle in db.bundles:
        ffmpeg_settings = FFMPEGSettings()
        ffmpeg_settings.output = Path(launch_args.output_folder) / bundle.name
        ffmpeg_settings.crf = launch_args.crf_quality
        ffmpeg_settings.preset = launch_args.preset

        bundle.status = BundleStatus.PROCESSING
        try:
            encode_bundle(bundle, ffmpeg_settings)
        except KeyboardInterrupt:
            bundle.status = BundleStatus.INTERRUPTED
            db.write()
            logger.info("Encoding interrupted.")
            return

        bundle.status = BundleStatus.DONE
        db.write()


if __name__ == "__main__":
    args = pars_args()
    run(args)
