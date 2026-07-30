"""Range-request capable file streaming for video playback."""

import mimetypes
import re
from pathlib import Path
from typing import Iterator

from fastapi import HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse

_CHUNK_SIZE = 1024 * 1024
_RANGE_RE = re.compile(r"bytes=(\d*)-(\d*)")


def stream_file(path: Path, request: Request) -> StreamingResponse | FileResponse:
    """Serve a file honouring the HTTP `Range` header so browsers can seek.

    Args:
        path: File to serve.
        request: Incoming request.

    Returns:
        Full `FileResponse` or a partial `StreamingResponse` (206).

    """
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"File `{path.name}` not found.")

    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    file_size = path.stat().st_size
    range_header = request.headers.get("range")

    if range_header is None:
        return FileResponse(path, media_type=media_type, headers={"accept-ranges": "bytes"})

    match = _RANGE_RE.fullmatch(range_header.strip())
    if match is None:
        raise HTTPException(status_code=416, detail="Malformed range header.")

    start_raw, end_raw = match.groups()
    if start_raw:
        start = int(start_raw)
        end = int(end_raw) if end_raw else file_size - 1
    else:
        # Suffix range: last N bytes.
        if not end_raw:
            raise HTTPException(status_code=416, detail="Malformed range header.")
        start = max(file_size - int(end_raw), 0)
        end = file_size - 1

    end = min(end, file_size - 1)
    if start > end or start >= file_size:
        raise HTTPException(status_code=416, detail="Requested range not satisfiable.")

    headers = {
        "content-range": f"bytes {start}-{end}/{file_size}",
        "accept-ranges": "bytes",
        "content-length": str(end - start + 1),
    }
    return StreamingResponse(_iter_range(path, start, end), status_code=206, media_type=media_type, headers=headers)


def _iter_range(path: Path, start: int, end: int) -> Iterator[bytes]:
    remaining = end - start + 1
    with open(path, "rb") as f:
        f.seek(start)
        while remaining > 0:
            chunk = f.read(min(_CHUNK_SIZE, remaining))
            if not chunk:
                break
            remaining -= len(chunk)
            yield chunk

