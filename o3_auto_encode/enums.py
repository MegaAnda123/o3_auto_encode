from enum import Enum


class Codec(Enum):
    X264 = "libx264"
    X265 = "libx265"
    NV264 = "h264_nvenc"
    NV265 = "h265_nvenc"
    AV1 = "libaom-av1"  # TODO implement av1 better, some settings are still incompatible with aom.

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


class LogLevel(Enum):
    """Custom log levels."""

    NOTSET = 0
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

    @classmethod
    def _missing_(cls, value: str):
        """Return the Enum member if the value matches the uppercase version of an Enum member value."""
        if not isinstance(value, str):
            raise ValueError(f"Can not convert '{value}' to loglevel.")
        for member in cls:
            if member.name == value.upper():
                return member
