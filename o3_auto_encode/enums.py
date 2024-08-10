from enum import Enum


class Codec(Enum):
    X264 = "libx264"
    X265 = "libx265"
    NV264 = "h264_nvenc"
    NV265 = "h265_nvenc"
    # TODO add AV1

    def __str__(self) -> str:
        return self.value


class EncodePreset(Enum):
    ULTRAFAST = "ultrafast"
    SUPERFAST = "superfast"
    VERYFAST = "veryfast"
    FASTER = "faster"
    FAST = "fast"
    MEDIUM = "medium"
    SLOW = "slow"
    SLOWER = "slower"
    VERYSLOW = "veryslow"
    PLACEBO = "placebo"

    def __str__(self) -> str:
        return self.value


class BundleStatus(Enum):
    FOUND = "found"
    PROCESSING = "processing"
    INTERRUPTED = "interrupted"
    DONE = "done"
