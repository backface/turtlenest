"""Validation and storage for user-supplied thumbnail images (base64 data URIs).

Thumbnails arrive from untrusted clients (Snap! / turtlecloud) as
``data:<mime>;base64,<payload>`` strings and are written to the media
directory, which is served from the application origin. Only small,
genuinely decodable raster images of a fixed set of types are accepted,
and they are always re-encoded as PNG, so the stored file never contains
client bytes (no trailing data, metadata or polyglots) and never takes its
type from the client-supplied MIME.

A thumbnail is only a preview: an invalid one is logged and dropped, it
never makes the project save fail.
"""

import base64
import binascii
import logging
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image

logger = logging.getLogger(__name__)

ALLOWED_THUMBNAIL_MIMES = {"image/png", "image/jpeg", "image/gif", "image/webp"}
ALLOWED_DECODED_FORMATS = {"PNG", "JPEG", "GIF", "WEBP"}

MAX_THUMBNAIL_BYTES = 5 * 1024 * 1024
MAX_THUMBNAIL_PIXELS = 4096 * 4096
# stored thumbnails are scaled down to fit in this box (aspect ratio kept)
THUMBNAIL_MAX_SIDE = 800


class ThumbnailError(ValueError):
    """Invalid thumbnail. ``str(exc)`` is a fixed, client-safe message;
    the underlying cause (e.g. Pillow's error) is chained as ``__cause__``."""


def parse_thumbnail_data_uri(value):
    """Validate a ``data:<mime>;base64,`` thumbnail and re-encode it.

    Returns the PNG bytes to store. Raises :class:`ThumbnailError` for
    anything that is not a small, valid image of an allowed type.
    """
    if not isinstance(value, str) or ";base64," not in value:
        raise ThumbnailError("thumbnail must be a base64 data URI")
    header, payload = value.split(";base64,", 1)
    header = header.strip()
    if not header.startswith("data:"):
        raise ThumbnailError("thumbnail must be a base64 data URI")
    if header[len("data:"):] not in ALLOWED_THUMBNAIL_MIMES:
        raise ThumbnailError("unsupported thumbnail type")

    # base64 taken from XML text may be wrapped or indented
    payload = "".join(payload.split())
    # reject before decoding: 4 base64 chars carry 3 bytes
    if len(payload) * 3 // 4 > MAX_THUMBNAIL_BYTES:
        raise ThumbnailError("thumbnail too large")
    try:
        data = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ThumbnailError("invalid thumbnail data") from exc
    if not data:
        raise ThumbnailError("empty thumbnail")

    try:
        with Image.open(BytesIO(data)) as image:
            image.verify()
        with Image.open(BytesIO(data)) as image:
            if image.format not in ALLOWED_DECODED_FORMATS:
                raise ThumbnailError("unsupported thumbnail type")
            if image.width * image.height > MAX_THUMBNAIL_PIXELS:
                raise ThumbnailError("thumbnail dimensions too large")
            image.load()  # decode all pixels; catches truncated/corrupt files
            image.thumbnail((THUMBNAIL_MAX_SIDE, THUMBNAIL_MAX_SIDE))
            if image.mode not in ("RGB", "RGBA", "L", "LA", "P"):
                image = image.convert("RGBA")
            out = BytesIO()
            image.save(out, format="PNG", optimize=True)
    except ThumbnailError:
        raise
    except Exception as exc:  # Pillow raises many types for bad input
        raise ThumbnailError("invalid image data") from exc
    return out.getvalue()


def save_project_thumbnail(project, value):
    """Validate ``value`` and store it as ``project``'s thumbnail.

    Returns True if a thumbnail was stored. An invalid thumbnail is logged
    and skipped (the project keeps its previous thumbnail).
    """
    if not value:
        return False
    try:
        png = parse_thumbnail_data_uri(value)
    except ThumbnailError as exc:
        logger.warning(
            "dropping invalid thumbnail for project %s: %s (%r)",
            project.pk,
            exc,
            exc.__cause__,
        )
        return False
    project.thumbnail.save(f"{project.slug}.png", ContentFile(png), save=True)
    return True
