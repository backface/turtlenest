import base64
from io import BytesIO
from unittest import mock

from django.test import SimpleTestCase
from PIL import Image

from apps.projects import thumbnails
from apps.projects.thumbnails import (
    THUMBNAIL_MAX_SIDE,
    ThumbnailError,
    parse_thumbnail_data_uri,
    save_project_thumbnail,
)


def data_uri(image_bytes, mime="image/png"):
    return f"data:{mime};base64," + base64.b64encode(image_bytes).decode()


def image_bytes(size=(20, 10), fmt="PNG", mode="RGB"):
    buf = BytesIO()
    Image.new(mode, size, "red").save(buf, format=fmt)
    return buf.getvalue()


def decode(png):
    with Image.open(BytesIO(png)) as image:
        image.load()
        return image.format, image.size


class ParseThumbnailTests(SimpleTestCase):
    def test_png_roundtrip(self):
        self.assertEqual(decode(parse_thumbnail_data_uri(data_uri(image_bytes()))), ("PNG", (20, 10)))

    def test_jpeg_is_reencoded_as_png(self):
        uri = data_uri(image_bytes(fmt="JPEG"), "image/jpeg")
        self.assertEqual(decode(parse_thumbnail_data_uri(uri))[0], "PNG")

    def test_claimed_mime_does_not_matter_for_output(self):
        # jpeg bytes declared as png: still a real image, stored as png
        uri = data_uri(image_bytes(fmt="JPEG"), "image/png")
        self.assertEqual(decode(parse_thumbnail_data_uri(uri))[0], "PNG")

    def test_whitespace_in_payload_is_accepted(self):
        header, payload = data_uri(image_bytes()).split(",", 1)
        wrapped = "\n".join(payload[i:i + 16] for i in range(0, len(payload), 16))
        uri = f"  {header},\n    {wrapped}\n  "
        self.assertEqual(decode(parse_thumbnail_data_uri(uri))[0], "PNG")

    def test_large_image_is_downscaled(self):
        png = parse_thumbnail_data_uri(data_uri(image_bytes(size=(1600, 400))))
        self.assertEqual(decode(png)[1], (THUMBNAIL_MAX_SIDE, THUMBNAIL_MAX_SIDE // 4))

    def test_trailing_bytes_are_stripped(self):
        polyglot = image_bytes() + b"<script>alert(1)</script>"
        png = parse_thumbnail_data_uri(data_uri(polyglot))
        self.assertNotIn(b"<script>", png)

    def test_cmyk_jpeg_is_converted(self):
        uri = data_uri(image_bytes(fmt="JPEG", mode="CMYK"), "image/jpeg")
        self.assertEqual(decode(parse_thumbnail_data_uri(uri))[0], "PNG")

    def assert_rejected(self, value, message):
        with self.assertRaises(ThumbnailError) as ctx:
            parse_thumbnail_data_uri(value)
        self.assertEqual(str(ctx.exception), message)

    def test_rejections_use_fixed_messages(self):
        self.assert_rejected(None, "thumbnail must be a base64 data URI")
        self.assert_rejected("not a data uri", "thumbnail must be a base64 data URI")
        self.assert_rejected("http://x;base64,AAAA", "thumbnail must be a base64 data URI")
        self.assert_rejected(data_uri(b"<b>x</b>", "text/html"), "unsupported thumbnail type")
        self.assert_rejected("data:image/png;base64,@@@@", "invalid thumbnail data")
        self.assert_rejected("data:image/png;base64,", "empty thumbnail")

    def test_pillow_errors_get_a_fixed_message(self):
        with self.assertRaises(ThumbnailError) as ctx:
            parse_thumbnail_data_uri(data_uri(b"<html>not an image</html>"))
        self.assertEqual(str(ctx.exception), "invalid image data")
        # Pillow's own error stays available for logging, not in the message
        self.assertIsNotNone(ctx.exception.__cause__)
        self.assertNotIn("PIL", str(ctx.exception))

    def test_truncated_image_is_rejected(self):
        self.assert_rejected(data_uri(image_bytes(size=(200, 200))[:-40]), "invalid image data")

    def test_unsupported_decoded_format_is_rejected(self):
        self.assert_rejected(data_uri(image_bytes(fmt="BMP")), "unsupported thumbnail type")

    def test_too_many_pixels_is_rejected(self):
        self.assert_rejected(data_uri(image_bytes(size=(5000, 5000))), "thumbnail dimensions too large")

    def test_oversized_payload_is_rejected_before_decoding(self):
        uri = "data:image/png;base64," + "A" * 64
        with mock.patch.object(thumbnails, "MAX_THUMBNAIL_BYTES", 10), \
                mock.patch.object(thumbnails.base64, "b64decode") as b64decode:
            self.assert_rejected(uri, "thumbnail too large")
        b64decode.assert_not_called()


class SaveProjectThumbnailTests(SimpleTestCase):
    def make_project(self):
        project = mock.Mock(slug="my-project", pk=1)
        return project

    def test_valid_thumbnail_is_saved_as_png(self):
        project = self.make_project()
        self.assertTrue(save_project_thumbnail(project, data_uri(image_bytes())))
        name, content = project.thumbnail.save.call_args.args
        self.assertEqual(name, "my-project.png")
        self.assertEqual(decode(content.read())[0], "PNG")

    def test_invalid_thumbnail_is_logged_and_skipped(self):
        project = self.make_project()
        with self.assertLogs("apps.projects.thumbnails", "WARNING") as logs:
            self.assertFalse(save_project_thumbnail(project, data_uri(b"junk")))
        project.thumbnail.save.assert_not_called()
        self.assertIn("invalid image data", logs.output[0])

    def test_missing_thumbnail_is_a_noop(self):
        project = self.make_project()
        self.assertFalse(save_project_thumbnail(project, None))
        self.assertFalse(save_project_thumbnail(project, ""))
        project.thumbnail.save.assert_not_called()
