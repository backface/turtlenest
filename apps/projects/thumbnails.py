"""Validation for user-supplied thumbnail images (base64 data URIs).

Thumbnails arrive from untrusted clients (Snap! / turtlecloud) as
``data:<mime>;base64,<payload>`` strings and are written to the media
directory, which is served from the application origin. Only small,
genuinely decodable raster images of a fixed set of types are accepted;
the on-disk extension is derived from the decoded content, never from
the client-supplied MIME type.
"""

import base64
import binascii
from io import BytesIO

from PIL import Image

ALLOWED_THUMBNAIL_MIMES = {
    "image/png": "png",
    "image/jpeg": "jpeg",
    "image/gif": "gif",
    "image/webp": "webp",
}

# Pillow decoded format name -> file extension.
FORMAT_EXTENSIONS = {"PNG": "png", "JPEG": "jpeg", "GIF": "gif", "WEBP": "webp"}

MAX_THUMBNAIL_BYTES = 5 * 1024 * 1024
MAX_THUMBNAIL_PIXELS = 4096 * 4096


def parse_thumbnail_data_uri(value):
    """Validate a ``data:<mime>;base64,`` thumbnail from an untrusted client.

    Returns ``(extension, raw_bytes)`` for the decoded image. Raises
    :class:`ValueError` for anything that is not a small, valid image of
    an allowed type (bad data-URI shape, disallowed MIME, bad base64,
    non-image bytes, oversized file or pixel count).
    """
    if not isinstance(value, str) or ";base64," not in value:
        raise ValueError("thumbnail must be a base64 data URI")
    header, payload = value.split(";base64,", 1)
    if not header.startswith("data:"):
        raise ValueError("thumbnail must be a data URI")
    mime = header[len("data:"):]
    if mime not in ALLOWED_THUMBNAIL_MIMES:
        raise ValueError(f"unsupported thumbnail type {mime!r}")
    try:
        data = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError(f"invalid thumbnail data: {exc}") from exc
    if not data:
        raise ValueError("empty thumbnail")
    if len(data) > MAX_THUMBNAIL_BYTES:
        raise ValueError("thumbnail too large")
    # Trust the bytes, not the claimed MIME: they must be a real image.
    try:
        with Image.open(BytesIO(data)) as image:
            image.verify()
    except Exception as exc:
        raise ValueError(f"invalid image data: {exc}") from exc
    with Image.open(BytesIO(data)) as image:
        if image.width * image.height > MAX_THUMBNAIL_PIXELS:
            raise ValueError("thumbnail dimensions too large")
        image.load()  # decode all pixels; catches truncated/corrupt files
        ext = FORMAT_EXTENSIONS.get(image.format)
    if ext is None:
        raise ValueError(f"unsupported decoded image format {image.format!r}")
    return ext, data
