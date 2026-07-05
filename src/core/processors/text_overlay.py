from __future__ import annotations

import logging

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

Color = tuple[int, int, int, int]

_FALLBACK_FONTS = ["arial.ttf", "malgun.ttf", "segoeui.ttf"]
_KOREAN_FONT = "malgun.ttf"  # 맑은 고딕 — 모든 최신 Windows에 기본 포함되는 한글 폰트
_LAYER_PADDING = 10

# 폰트 파일에 실제 Bold/Italic 변형이 없는 경우가 많아(사용자가 추가한 커스텀 폰트 등),
# 폰트 교체 없이 항상 동작하는 방식으로 굵게/기울임을 흉내낸다.
_BOLD_STROKE_RATIO = 1 / 22  # 폰트 크기 대비 획 두께 비율
_ITALIC_SHEAR = 0.22  # 기울임 정도(라디안 아님, 어파인 시어 계수)


def _contains_hangul(text: str) -> bool:
    return any(
        "가" <= ch <= "힣"  # 한글 음절
        or "ᄀ" <= ch <= "ᇿ"  # 한글 자모
        or "㄰" <= ch <= "㆏"  # 한글 호환 자모
        for ch in text
    )


def _load_font(font_path: str | None, size: int, text: str = "") -> ImageFont.FreeTypeFont:
    candidates: list[str] = []
    if _contains_hangul(text):
        # PIL은 Qt와 달리 폰트가 지원하지 않는 글자를 다른 폰트로 자동 대체하지 않는다.
        # 사용자가 고른 폰트(예: Arial)가 한글을 지원하지 않으면 텍스트 전체가 네모(tofu)로만
        # 나오므로, 한글이 섞여 있으면 한글 지원이 확실한 폰트를 먼저 시도한다.
        candidates.append(_KOREAN_FONT)
    if font_path:
        candidates.append(font_path)
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


def _italicize_layer(layer: Image.Image, shear: float = _ITALIC_SHEAR) -> Image.Image:
    """텍스트 레이어를 어파인 시어 변환으로 기울여 이탤릭체처럼 보이게 한다.

    폰트 파일에 실제 Italic 변형이 있는지와 무관하게 항상 동작하도록, 폰트를
    바꾸는 대신 렌더링된 이미지 자체를 기울인다.
    """
    width, height = layer.size
    xshift = round(shear * height)
    return layer.transform(
        (width + xshift, height),
        Image.AFFINE,
        (1, shear, -xshift, 0, 1, 0),
        resample=Image.BICUBIC,
        fillcolor=(0, 0, 0, 0),
    )


def _render_text_layer(
    text: str,
    font: ImageFont.FreeTypeFont,
    color: Color,
    shadow: bool,
    bold: bool = False,
    italic: bool = False,
) -> Image.Image:
    """텍스트만 담긴 투명 레이어를 만든다.

    캔버스 드래그 미리보기(render_text_preview)와 최종 합성(add_text)이 이 함수를 함께
    써서, 미리보기에 보이는 모양과 실제 적용 결과의 글자 간격/모양이 완전히 같도록 한다
    (Qt 폰트 렌더러로 미리보기를 그리면 PIL/FreeType 결과와 자간이 달라질 수 있었음).
    """
    stroke_width = max(1, round(font.size * _BOLD_STROKE_RATIO)) if bold else 0

    dummy = Image.new("RGBA", (1, 1))
    bbox = ImageDraw.Draw(dummy).textbbox((0, 0), text, font=font, stroke_width=stroke_width)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]

    layer = Image.new("RGBA", (text_w + _LAYER_PADDING * 2, text_h + _LAYER_PADDING * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    origin = (_LAYER_PADDING - bbox[0], _LAYER_PADDING - bbox[1])
    if shadow:
        shadow_color = (0, 0, 0, 160)
        draw.text(
            (origin[0] + 2, origin[1] + 2),
            text,
            font=font,
            fill=shadow_color,
            stroke_width=stroke_width,
            stroke_fill=shadow_color,
        )
    draw.text(origin, text, font=font, fill=color, stroke_width=stroke_width, stroke_fill=color)

    if italic:
        layer = _italicize_layer(layer)
    return layer


def render_text_preview(
    text: str,
    font_path: str | None = None,
    size: int = 48,
    color: Color = (255, 255, 255, 255),
    shadow: bool = True,
    bold: bool = False,
    italic: bool = False,
) -> Image.Image:
    """캔버스 드래그 오버레이용 텍스트 레이어. add_text()와 동일한 렌더링 경로를 쓴다."""
    display_text = text if text else " "
    font = _load_font(font_path, size, display_text)
    return _render_text_layer(display_text, font, color, shadow, bold=bold, italic=italic)


def add_text(
    image: Image.Image,
    text: str,
    position: tuple[int, int] = (20, 20),
    font_path: str | None = None,
    size: int = 48,
    color: Color = (255, 255, 255, 255),
    rotation: float = 0.0,
    shadow: bool = True,
    bold: bool = False,
    italic: bool = False,
) -> Image.Image:
    """이미지에 텍스트를 오버레이한다. position은 (패딩 포함) 레이어의 좌상단 기준 좌표."""
    if not text:
        raise ValueError("text는 비어 있을 수 없습니다.")
    if size <= 0:
        raise ValueError("size는 0보다 커야 합니다.")

    base = image.convert("RGBA")
    font = _load_font(font_path, size, text)
    layer = _render_text_layer(text, font, color, shadow, bold=bold, italic=italic)

    if rotation != 0:
        layer = layer.rotate(rotation, expand=True, resample=Image.BICUBIC)

    base.paste(layer, position, layer)
    return base
