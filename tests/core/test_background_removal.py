import io
from unittest.mock import patch

from PIL import Image

from core.processors import background_removal


def _fake_remove(data: bytes, session=None) -> bytes:
    image = Image.open(io.BytesIO(data)).convert("RGBA")
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def test_remove_background_mocked(sample_rgb_image):
    background_removal._session = None
    with (
        patch("rembg.remove", side_effect=_fake_remove),
        patch("rembg.new_session", return_value="fake-session"),
    ):
        result = background_removal.remove_background(sample_rgb_image)
    assert result.mode == "RGBA"
    assert result.size == sample_rgb_image.size


def test_replace_background_with_color(sample_rgba_image):
    result = background_removal.replace_background(sample_rgba_image, (0, 255, 0))
    assert result.mode == "RGBA"
    assert result.size == sample_rgba_image.size
