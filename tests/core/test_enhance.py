import pytest

from core.processors.enhance import FILTER_PRESETS, apply_adjustments, apply_filter


def test_apply_adjustments_identity_returns_same_size(sample_rgb_image):
    result = apply_adjustments(sample_rgb_image)
    assert result.size == sample_rgb_image.size


def test_apply_adjustments_brightness_changes_pixels(sample_rgb_image):
    result = apply_adjustments(sample_rgb_image, brightness=1.5)
    assert result.getpixel((0, 0)) != sample_rgb_image.getpixel((0, 0))


def test_apply_filter_all_presets_run(sample_rgb_image):
    for name in FILTER_PRESETS:
        result = apply_filter(sample_rgb_image, name)
        assert result.size == sample_rgb_image.size


def test_apply_filter_unknown_raises(sample_rgb_image):
    with pytest.raises(ValueError):
        apply_filter(sample_rgb_image, "nope")


def test_apply_adjustments_preserves_transparent_alpha(sample_rgba_image):
    # 배경 제거 후처럼 알파가 0인 이미지에 보정을 적용해도 투명도가 깨지면 안 된다.
    transparent = sample_rgba_image.copy()
    alpha = transparent.split()[-1].point(lambda _: 0)
    transparent.putalpha(alpha)

    result = apply_adjustments(transparent, brightness=1.4, contrast=1.3, saturation=0.7)

    assert result.mode == "RGBA"
    assert result.split()[-1].getextrema() == (0, 0)


def test_mono_filter_preserves_alpha(sample_rgba_image):
    transparent = sample_rgba_image.copy()
    transparent.putalpha(transparent.split()[-1].point(lambda _: 0))

    result = apply_filter(transparent, "mono")

    assert result.mode == "RGBA"
    assert result.split()[-1].getextrema() == (0, 0)
