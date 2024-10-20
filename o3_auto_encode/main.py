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
    logger.debug(str(Path.cwd()))
    ffmpeg_settings = FFMPEGSettings(launch_args.config_path)
    db = FileDataBase(launch_args.json_path, generate_bundles(ffmpeg_settings.input))

    for bundle in db.bundles:
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
