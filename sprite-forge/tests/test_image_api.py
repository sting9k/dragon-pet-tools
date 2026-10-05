from __future__ import annotations

import argparse
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "generate2dsprite" / "scripts"))
import image_api  # noqa: E402

ARGS = argparse.Namespace(resolution="2k", aspect="1:1", size="1024x1024")


def png(img: Image.Image) -> bytes:
    out = io.BytesIO()
    img.save(out, "PNG")
    return out.getvalue()


class RequestBodyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ref = Path(self.tmp.name) / "ref.png"
        self.ref.write_bytes(png(Image.new("RGB", (4, 4), (1, 2, 3))))

    def test_json_body_sends_references_inline(self) -> None:
        body, kind = image_api.json_body("m", "a prompt", [self.ref], ARGS)
        sent = json.loads(body)
        self.assertEqual(kind, "application/json")
        self.assertEqual((sent["model"], sent["prompt"], sent["aspect_ratio"]), ("m", "a prompt", "1:1"))
        self.assertTrue(sent["images"][0].startswith("data:image/png;base64,"))

    def test_json_body_without_references_has_no_images(self) -> None:
        self.assertNotIn("images", json.loads(image_api.json_body("m", "p", [], ARGS)[0]))

    def test_multipart_body_carries_fields_and_file(self) -> None:
        body, kind = image_api.multipart_body("m", "a prompt", [self.ref], ARGS)
        mark = kind.split("boundary=")[1].encode()
        self.assertEqual(body.count(b"--" + mark), 6)  # four fields, one file, the closing mark
        self.assertIn(b'name="size"\r\n\r\n1024x1024', body)
        self.assertIn(b'filename="ref.png"', body)
        self.assertIn(self.ref.read_bytes(), body)


class TidyTests(unittest.TestCase):
    def test_snaps_haze_and_near_opaque_alpha(self) -> None:
        img = Image.new("RGBA", (3, 1))
        img.putdata([(9, 9, 9, 1), (9, 9, 9, 120), (9, 9, 9, 252)])
        tidied = Image.open(io.BytesIO(image_api.tidy(png(img))))
        self.assertEqual(list(tidied.getchannel("A").getdata()), [0, 120, 255])

    def test_leaves_opaque_pictures_untouched(self) -> None:
        picture = png(Image.new("RGB", (4, 4), (255, 0, 255)))
        self.assertIs(image_api.tidy(picture), picture)


class SettingsTests(unittest.TestCase):
    def test_missing_key_stops_before_any_request(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(image_api, "load_env"), self.assertRaises(SystemExit) as stop:
            image_api.settings()
        self.assertIn("IMAGE_KEY", str(stop.exception))

    def test_missing_endpoint_stops_before_any_request(self) -> None:
        with mock.patch.dict(os.environ, {"IMAGE_KEY": "k"}, clear=True), mock.patch.object(image_api, "load_env"), self.assertRaises(SystemExit) as stop:
            image_api.settings()
        self.assertIn("IMAGE_API", str(stop.exception))

    def test_generations_endpoint_follows_the_edits_endpoint(self) -> None:
        with mock.patch.dict(os.environ, {"IMAGE_KEY": "k", "IMAGE_API": "https://x.test/v1/images/edits"}, clear=True), mock.patch.object(image_api, "load_env"):
            self.assertEqual(image_api.settings()["generate"], "https://x.test/v1/images/generations")


if __name__ == "__main__":
    unittest.main()
