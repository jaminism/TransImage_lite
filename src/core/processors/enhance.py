from __future__ import annotations

from PIL import Image, ImageEnhance, ImageOps


def _enhance(enhancer_cls: type, image: Image.Image, factor: float) -> Image.Image:
    """RGBA 이미지의 알파 채널을 보존하며 ImageEnhance를 적용한다.

    PIL의 ImageEnhance는 알파 채널까지 다른 밴드와 함께 블렌딩하므로, 그대로 쓰면
    배경 제거 후 보정 시 투명 영역이 부분적으로 불투명해지는 문제가 있다.
    """
    if factor == 1.0:
        return image
    if image.mode == "RGBA":
        alpha = image.split()[-1]
        enhanced_rgb = enhancer_cls(image.convert("RGB")).enhance(factor)
        return Image.merge("RGBA", (*enhanced_rgb.split(), alpha))
    return enhancer_cls(image).enhance(factor)


def adjust_brightness(image: Image.Image, factor: float) -> Image.Image:
    return _enhance(ImageEnhance.Brightness, image, factor)


def adjust_contrast(image: Image.Image, factor: float) -> Image.Image:
    return _enhance(ImageEnhance.Contrast, image, factor)


def adjust_saturation(image: Image.Image, factor: float) -> Image.Image:
    return _enhance(ImageEnhance.Color, image, factor)


def apply_adjustments(
    image: Image.Image,
    brightness: float = 1.0,
    contrast: float = 1.0,
    saturation: float = 1.0,
) -> Image.Image:
    """밝기/대비/채도를 한 번에 적용한다. 각 값은 1.0이 원본(변화 없음)."""
    result = image
    if brightness != 1.0:
        result = adjust_brightness(result, brightness)
    if contrast != 1.0:
        result = adjust_contrast(result, contrast)
    if saturation != 1.0:
        result = adjust_saturation(result, saturation)
    return result


def _warm(image: Image.Image) -> Image.Image:
    r, g, b = image.convert("RGB").split()[:3]
    r = r.point(lambda v: min(255, int(v * 1.12)))
    b = b.point(lambda v: int(v * 0.9))
    channels = [r, g, b]
    if image.mode == "RGBA":
        channels.append(image.split()[-1])
        return Image.merge("RGBA", channels)
    return Image.merge("RGB", channels)


def _cool(image: Image.Image) -> Image.Image:
    r, g, b = image.convert("RGB").split()[:3]
    r = r.point(lambda v: int(v * 0.9))
    b = b.point(lambda v: min(255, int(v * 1.12)))
    channels = [r, g, b]
    if image.mode == "RGBA":
        channels.append(image.split()[-1])
        return Image.merge("RGBA", channels)
    return Image.merge("RGB", channels)


def _vintage(image: Image.Image) -> Image.Image:
    faded = adjust_saturation(image, 0.6)
    return adjust_contrast(faded, 0.9)


def _mono(image: Image.Image) -> Image.Image:
    alpha = image.split()[-1] if image.mode == "RGBA" else None
    gray = ImageOps.grayscale(image)
    contrasted = adjust_contrast(gray, 1.3).convert("RGB")
    if alpha is not None:
        return Image.merge("RGBA", (*contrasted.split(), alpha))
    return contrasted


FILTER_PRESETS = {
    "warm": _warm,
    "cool": _cool,
    "vintage": _vintage,
    "mono": _mono,
}


def apply_filter(image: Image.Image, preset_name: str) -> Image.Image:
    if preset_name not in FILTER_PRESETS:
        raise ValueError(f"알 수 없는 필터 프리셋입니다: {preset_name}")
    return FILTER_PRESETS[preset_name](image)
