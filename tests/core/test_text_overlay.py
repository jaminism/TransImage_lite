import pytest

from core.processors.text_overlay import add_text


def test_add_text_returns_rgba(sample_rgb_image):
    result = add_text(sample_rgb_image, "Hi", position=(0, 0), size=10)
    assert result.mode == "RGBA"
    assert result.size == sample_rgb_image.size


def test_add_text_empty_raises(sample_rgb_image):
    with pytest.raises(ValueError):
        add_text(sample_rgb_image, "", size=10)


def test_add_text_rotation(sample_rgb_image):
    result = add_text(sample_rgb_image, "Hi", size=10, rotation=45)
    assert result.mode == "RGBA"
