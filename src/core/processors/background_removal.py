from __future__ import annotations

import io
import logging

from PIL import Image

logger = logging.getLogger(__name__)

_session = None


def _get_session():
    global _session
    if _session is None:
        from rembg import new_session

        logger.info("rembg u2net 세션을 생성합니다 (최초 1회, 모델 다운로드 필요할 수 있음).")
        _session = new_session("u2net")
    return _session


def remove_background(image: Image.Image) -> Image.Image:
    """피사체만 남기고 배경을 투명하게 만든다 (RGBA 반환)."""
    try:
        from rembg import remove
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("배경 제거 기능을 사용할 수 없습니다 (rembg 미설치).") from exc

    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format="PNG")

    try:
        session = _get_session()
        result_bytes = remove(buffer.getvalue(), session=session)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"배경 제거 처리 중 오류가 발생했습니다: {exc}") from exc

    return Image.open(io.BytesIO(result_bytes)).convert("RGBA")


def replace_background(foreground_rgba: Image.Image, background: Image.Image | tuple[int, int, int]) -> Image.Image:
    """배경 제거된 RGBA 이미지를 단색 또는 다른 이미지 배경과 합성한다."""
    size = foreground_rgba.size
    if isinstance(background, tuple):
        base = Image.new("RGBA", size, background + (255,) if len(background) == 3 else background)
    else:
        base = background.convert("RGBA").resize(size, Image.LANCZOS)
    return Image.alpha_composite(base, foreground_rgba)
