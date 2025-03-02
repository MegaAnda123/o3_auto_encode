import signal
from pathlib import Path
from types import FrameType

from o3_auto_encode import logger, utils
from o3_auto_encode.args_parser import LaunchArguments, pars_args
from o3_auto_encode.db import FileDataBase
from o3_auto_encode.encoder import encode_bundle
from o3_auto_encode.enums import BundleStatus
from o3_auto_encode.ffmpeg_settings import FFMPEGSettings
from o3_auto_encode.file_manager import generate_bundles


def run(launch_args: LaunchArguments) -> None:
    logger.debug(str(launch_args))
    logger.debug(str(Path.cwd()))
    ffmpeg_settings = FFMPEGSettings(launch_args.config_path)
    db = FileDataBase(launch_args.json_path, generate_bundles(ffmpeg_settings.input))

    for bundle in db.bundles:
        if bundle.status == BundleStatus.INTERRUPTED:
            utils.clean_up_interrupted_video(bundle, ffmpeg_settings.output)
        bundle.status = BundleStatus.PROCESSING
        try:
            encode_bundle(bundle, ffmpeg_settings)
        except (KeyboardInterrupt, NotADirectoryError):
            bundle.status = BundleStatus.INTERRUPTED
            db.write()
            logger.info("Encoding interrupted.")
            # TODO resume interrupted videos.
            return

        bundle.status = BundleStatus.DONE
        db.write()


def exit_gracefully(signum: int, frame: FrameType):
    """Gracefully exit when sigterm is called by docker."""
    logger.debug(str(signum))
    logger.debug(str(frame))
    raise SystemExit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)

    args = pars_args()
    run(args)
