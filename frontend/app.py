"""FastAPI application serving encode stats, progress and media for the frontend."""

from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles

from frontend.config import Settings, get_settings
from frontend.media import stream_file
from frontend.serializers import serialize_bundle
from o3_auto_encode import progress
from o3_auto_encode.db import FileDataBase
from o3_auto_encode.ffmpeg_settings import FFMPEGSettings
from o3_auto_encode.file_manager import Bundle

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="o3 auto encode", description="Encode progress dashboard.")


def _load_bundles(settings: Settings) -> list[Bundle]:
    """Load bundles from the database file, empty list when it does not exist yet."""
    return FileDataBase(settings.db_path).bundles


def _fallback_output(settings: Settings) -> Path | None:
    """Output folder from the encoder config, used for bundles without stored config."""
    try:
        return FFMPEGSettings(settings.config_path).output
    except (FileNotFoundError, ValueError):
        return None


def _find_bundle(bundles: list[Bundle], name: str) -> Bundle:
    for bundle in bundles:
        if bundle.name == name:
            return bundle
    raise HTTPException(status_code=404, detail=f"Bundle `{name}` not found.")


@app.get("/api/health")
def health(settings: Settings = Depends(get_settings)) -> dict:
    """Service health and resolved paths."""
    return {
        "status": "ok",
        "db_path": str(settings.db_path),
        "db_exists": settings.db_path.is_file(),
        "config_path": str(settings.config_path),
    }


@app.get("/api/bundles")
def list_bundles(settings: Settings = Depends(get_settings)) -> dict:
    """List every bundle with its stats."""
    fallback = _fallback_output(settings)
    bundles = _load_bundles(settings)
    return {"bundles": [serialize_bundle(bundle, fallback) for bundle in bundles]}


@app.get("/api/bundles/{name}")
def get_bundle(name: str, settings: Settings = Depends(get_settings)) -> dict:
    """Get a single bundle with its stats."""
    bundle = _find_bundle(_load_bundles(settings), name)
    return serialize_bundle(bundle, _fallback_output(settings))


@app.get("/api/progress")
def get_progress(settings: Settings = Depends(get_settings)) -> dict:
    """Current encode progress heartbeat."""
    data = progress.read_progress(progress.progress_path_for(settings.db_path))
    if data is None:
        return {"bundle": None, "state": "unknown", "stale": True}
    return data


@app.get("/api/media/clip/{bundle_name}/{clip_name}")
def get_clip_media(bundle_name: str, clip_name: str, request: Request, settings: Settings = Depends(get_settings)):
    """Stream a source clip. Only clips referenced by the database can be served."""
    bundle = _find_bundle(_load_bundles(settings), bundle_name)
    for clip in bundle.clips:
        if clip.name == clip_name:
            return stream_file(clip.path, request)
    raise HTTPException(status_code=404, detail=f"Clip `{clip_name}` not found in bundle `{bundle_name}`.")


@app.get("/api/media/output/{bundle_name}")
def get_output_media(bundle_name: str, request: Request, settings: Settings = Depends(get_settings)):
    """Stream the encoded output. Unavailable while encoding is unfinished."""
    bundle = _find_bundle(_load_bundles(settings), bundle_name)
    if not bundle.is_encoded:
        raise HTTPException(status_code=409, detail=f"Bundle `{bundle_name}` is not encoded yet.")

    output_path = bundle.output_path(_fallback_output(settings))
    if output_path is None:
        raise HTTPException(status_code=404, detail="Output folder is unknown.")
    return stream_file(output_path, request)


# Mounted last so the API routes take precedence.
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

