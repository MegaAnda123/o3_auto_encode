import logging

import typer

from o3_auto_encode.enums import LogLevel

_level = LogLevel.DEBUG.value


def set_level(level: LogLevel | str | int) -> None:
    global _level
    _level = LogLevel(level).value


def _format_message(message: str, level: LogLevel) -> str:
    """Format string to have message level on start of every line."""
    lines = message.splitlines(keepends=True)
    lines = lines if len(lines) > 1 else [""] + lines
    lines = lines if lines[0] in ["", "\n"] else [""] + lines
    return f"{level.name}: ".join(lines)


def debug(message: str) -> None:
    """Log message with severity DEBUG."""
    if _level <= logging.DEBUG:
        typer.secho(_format_message(message, LogLevel.DEBUG), fg=typer.colors.BLUE)


def info(message: str) -> None:
    """Log message with severity INFO."""
    if _level <= logging.INFO:
        typer.secho(_format_message(message, LogLevel.INFO), fg=typer.colors.WHITE)


def warning(message: str) -> None:
    """Log message with severity WARNING."""
    if _level <= logging.WARNING:
        typer.secho(_format_message(message, LogLevel.WARNING), fg=typer.colors.YELLOW)


def error(message: str) -> None:
    """Log message with severity ERROR."""
    if _level <= logging.ERROR:
        typer.secho(_format_message(message, LogLevel.ERROR), fg=typer.colors.RED, err=True)


def critical(message: str) -> None:
    """Log message with severity CRITICAL."""
    if _level <= logging.CRITICAL:
        typer.secho(_format_message(message, LogLevel.CRITICAL), fg=typer.colors.RED, err=True)
