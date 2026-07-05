from __future__ import annotations

import logging

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

Color = tuple[int, int, int, int]

_FALLBACK_FONTS = ["arial.ttf", "malgun.ttf", "segoeui.ttf"]


def _load_font(font_path: str | None, size: int) -> ImageFont.FreeTypeFont:
    candidates = [font_path] if font_path else []
    candidates.extend(_FALLBACK_FONTS)
    for candidate in candidates:
        if not candidate:
            continue
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    logger.warning("지정한 폰트를 찾을 수 없어 기본 폰트로 대체합니다.")
    return ImageFont.load_default(size=size)


def add_text(
    image: Image.Image,
    text: str,
    position: tuple[int, int] = (20, 20),
    font_path: str | None = None,
    size: int = 48,
    color: Color = (255, 255, 255, 255),
    rotation: float = 0.0,
    shadow: bool = True,
) -> Image.Image:
    """이미지에 텍스트를 오버레이한다. position은 좌상단 기준 좌표."""
    if not text:
        raise ValueError("text는 비어 있을 수 없습니다.")
    if size <= 0:
        raise ValueError("size는 0보다 커야 합니다.")

    base = image.convert("RGBA")
    font = _load_font(font_path, size)

    draw = ImageDraw.Draw(base)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]

    if rotation == 0:
        if shadow:
            shadow_pos = (position[0] + 2, position[1] + 2)
            draw.text(shadow_pos, text, font=font, fill=(0, 0, 0, 160))
        draw.text(position, text, font=font, fill=color)
        return base

    layer = Image.new("RGBA", (text_w + 20, text_h + 20), (0, 0, 0, 0))
    layer_draw = ImageDraw.Draw(layer)
    if shadow:
        layer_draw.text((12, 12), text, font=font, fill=(0, 0, 0, 160))
    layer_draw.text((10, 10), text, font=font, fill=color)
    rotated = layer.rotate(rotation, expand=True, resample=Image.BICUBIC)
    base.paste(rotated, position, rotated)
    return base
