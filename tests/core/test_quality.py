import pytest

from core.processors.quality import denoise, sharpen, upscale


def test_denoise_rgb(sample_rgb_image):
    result = denoise(sample_rgb_image, strength=5)
    assert result.size == sample_rgb_image.size
    assert result.mode == "RGB"


def test_denoise_rgba_preserves_alpha(sample_rgba_image):
    result = denoise(sample_rgba_image, strength=5)
    assert result.mode == "RGBA"
    assert result.size == sample_rgba_image.size


def test_denoise_invalid_strength_raises(sample_rgb_image):
    with pytest.raises(ValueError):
        denoise(sample_rgb_image, strength=0)


def test_sharpen(sample_rgb_image):
    result = sharpen(sample_rgb_image, amount=1.5)
    assert result.size == sample_rgb_image.size


def test_sharpen_negative_raises(sample_rgb_image):
    with pytest.raises(ValueError):
        sharpen(sample_rgb_image, amount=-1)


def test_upscale_without_model_falls_back_to_lanczos(sample_rgb_image):
    result = upscale(sample_rgb_image, scale=2)
    w, h = sample_rgb_image.size
    assert result.size == (w * 2, h * 2)


def test_upscale_invalid_scale_raises(sample_rgb_image):
    with pytest.raises(ValueError):
        upscale(sample_rgb_image, scale=5)
