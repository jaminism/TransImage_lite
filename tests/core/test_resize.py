import pytest

from core.processors.resize import PRESETS, crop_to_fit, resize_image, resize_to_preset


def test_resize_keep_ratio_width_only(sample_rgb_image):
    result = resize_image(sample_rgb_image, width=15)
    assert result.size == (15, 10)


def test_resize_no_ratio(sample_rgb_image):
    result = resize_image(sample_rgb_image, width=10, height=10, keep_ratio=False)
    assert result.size == (10, 10)


def test_resize_zero_size_raises(sample_rgb_image):
    with pytest.raises(ValueError):
        resize_image(sample_rgb_image, width=0)


def test_resize_missing_dims_raises(sample_rgb_image):
    with pytest.raises(ValueError):
        resize_image(sample_rgb_image)


def test_resize_to_preset(sample_rgb_image):
    result = resize_to_preset(sample_rgb_image, "instagram_square")
    assert result.size == PRESETS["instagram_square"]


def test_resize_to_unknown_preset_raises(sample_rgb_image):
    with pytest.raises(ValueError):
        resize_to_preset(sample_rgb_image, "nope")


def test_crop_to_fit(sample_rgb_image):
    result = crop_to_fit(sample_rgb_image, 10, 10)
    assert result.size == (10, 10)
