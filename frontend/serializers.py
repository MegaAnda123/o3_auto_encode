"""Conversion of `Bundle` objects into frontend friendly payloads.

Encoded output stats and the encode settings are only emitted for bundles that finished
encoding (`done`/`verified`), so the UI can never render numbers for a partial file.
"""

from pathlib import Path
from typing import Any
from urllib.parse import quote

from o3_auto_encode.file_manager import Bundle, Clip


def serialize_clip(bundle: Bundle, clip: Clip) -> dict[str, Any]:
    """Serialize a single source clip."""
    return {
        "name": clip.name,
        "duration": clip.duration,
        "duration_s": clip.duration_s,
        "creation_time": clip.creation_time,
        "frames": clip.frames,
        "size": clip.size,
        "resolution": clip.resolution,
        "bitrate": clip.bitrate,
        "fps": clip.fps,
        "codec": clip.codec,
        "media_url": f"/api/media/clip/{quote(bundle.name)}/{quote(clip.name)}",
    }


def serialize_bundle(bundle: Bundle, fallback_output: Path | str | None = None) -> dict[str, Any]:
    """Serialize a bundle including source stats and, when finished, encoded stats.

    Args:
        bundle: Bundle to serialize.
        fallback_output: Output folder used when the bundle has no stored config.

    Returns:
        Frontend payload for the bundle.

    """
    total_size = bundle.total_size

    payload: dict[str, Any] = {
        "name": bundle.name,
        "status": str(bundle.status),
        "creation_time": bundle.creation_time,
        "clip_count": len(bundle.clips),
        "total_frames": bundle.total_frames,
        "total_size": total_size,
        "resolution": bundle.clips[0].resolution if bundle.clips else None,
        "clips": [serialize_clip(bundle, clip) for clip in bundle.clips],
        "encoded": None,
        "settings": None,
    }

    if not bundle.is_encoded:
        # Encoding not finished: no output stats and no settings, the UI shows progress instead.
        return payload

    payload["encoded"] = _serialize_encoded(bundle, total_size, fallback_output)
    payload["settings"] = _serialize_settings(bundle)
    return payload


def _serialize_encoded(bundle: Bundle, total_size: int | None, fallback_output: Path | str | None) -> dict[str, Any]:
    encoded = dict(bundle.encoded or {})
    output_path = bundle.output_path(fallback_output)

    size = encoded.get("size")
    if size is None and output_path is not None and output_path.is_file():
        size = output_path.stat().st_size

    savings_pct = None
    if size is not None and total_size:
        savings_pct = round((1 - size / total_size) * 100, 2)

    return {
        "size": size,
        "resolution": encoded.get("resolution"),
        "bitrate": encoded.get("bitrate"),
        "fps": encoded.get("fps"),
        "codec": encoded.get("codec"),
        "frames": encoded.get("frames"),
        "savings_pct": savings_pct,
        "exists": bool(output_path and output_path.is_file()),
        "media_url": f"/api/media/output/{quote(bundle.name)}",
    }


def _serialize_settings(bundle: Bundle) -> dict[str, Any] | None:
    config = bundle.config or {}
    if not config:
        return None
    return {
        "codec": config.get("codec"),
        "preset": config.get("preset"),
        "crf": config.get("crf"),
        "output": config.get("output"),
        "command": config.get("command"),
    }

