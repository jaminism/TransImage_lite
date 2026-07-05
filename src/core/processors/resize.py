from __future__ import annotations

from PIL import Image, ImageOps

# (width, height) — 300dpi 기준 인쇄용 프리셋 포함
PRESETS: dict[str, tuple[int, int]] = {
    "instagram_square": (1080, 1080),
    "instagram_story": (1080, 1920),
    "youtube_thumbnail": (1280, 720),
    "print_4x6in_300dpi": (1200, 1800),
    "print_a4_300dpi": (2480, 3508),
}


def resize_image(
    image: Image.Image,
    width: int | None = None,
    height: int | None = None,
    keep_ratio: bool = True,
) -> Image.Image:
    """비율 고정/자유 리사이즈. width/height 중 하나 이상 필요."""
    if width is None and height is None:
        raise ValueError("width 또는 height 중 하나는 지정해야 합니다.")
    if (width is not None and width <= 0) or (height is not None and height <= 0):
        raise ValueError("width/height는 0보다 커야 합니다.")

    orig_w, orig_h = image.size

    if keep_ratio:
        if width is not None and height is None:
            height = round(orig_h * width / orig_w)
        elif height is not None and width is None:
            width = round(orig_w * height / orig_h)
        elif width is not None and height is not None:
            # 둘 다 주어지면 짧은 변에 맞춰 비율을 유지한다
            ratio = min(width / orig_w, height / orig_h)
            width, height = round(orig_w * ratio), round(orig_h * ratio)
    else:
        width = width if width is not None else orig_w
        height = height if height is not None else orig_h

    return image.resize((width, height), Image.LANCZOS)


def resize_to_preset(image: Image.Image, preset_name: str) -> Image.Image:
    """프리셋 크기에 중앙 크롭으로 맞춘다 (비율이 다른 경우 크롭)."""
    if preset_name not in PRESETS:
        raise ValueError(f"알 수 없는 프리셋입니다: {preset_name}")
    size = PRESETS[preset_name]
    return ImageOps.fit(image, size, Image.LANCZOS, centering=(0.5, 0.5))


def crop_to_fit(image: Image.Image, width: int, height: int) -> Image.Image:
    """목표 크기에 중앙 크롭 리사이즈."""
    if width <= 0 or height <= 0:
        raise ValueError("width/height는 0보다 커야 합니다.")
    return ImageOps.fit(image, (width, height), Image.LANCZOS, centering=(0.5, 0.5))
