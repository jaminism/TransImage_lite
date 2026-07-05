from __future__ import annotations

import logging

import numpy as np
from PIL import Image, ImageEnhance

logger = logging.getLogger(__name__)

try:
    import cv2

    _CV2_AVAILABLE = True
except ImportError:  # pragma: no cover - opencv should normally be installed
    _CV2_AVAILABLE = False


def _require_cv2() -> None:
    if not _CV2_AVAILABLE:
        raise RuntimeError("opencv-python-headless가 설치되어 있지 않습니다.")


def _to_cv_bgr(image: Image.Image) -> tuple[np.ndarray, np.ndarray | None]:
    """PIL RGB(A) -> OpenCV BGR ndarray, 알파 채널은 별도로 반환."""
    rgba = image.convert("RGBA")
    array = np.array(rgba)
    bgr = array[:, :, :3][:, :, ::-1].copy()
    alpha = array[:, :, 3].copy() if image.mode == "RGBA" else None
    return bgr, alpha


def _to_pil(bgr: np.ndarray, alpha: np.ndarray | None, original_mode: str) -> Image.Image:
    rgb = bgr[:, :, ::-1]
    if alpha is not None:
        rgba = np.dstack([rgb, alpha])
        return Image.fromarray(rgba, mode="RGBA")
    result = Image.fromarray(rgb, mode="RGB")
    return result.convert(original_mode) if original_mode not in ("RGB", "RGBA") else result


def denoise(image: Image.Image, strength: int = 10) -> Image.Image:
    """cv2.fastNlMeansDenoisingColored 기반 노이즈 제거. strength: 5~15 권장."""
    _require_cv2()
    if not (0 < strength <= 30):
        raise ValueError("strength는 0~30 사이여야 합니다.")
    bgr, alpha = _to_cv_bgr(image)
    denoised = cv2.fastNlMeansDenoisingColored(bgr, None, strength, strength, 7, 21)
    return _to_pil(denoised, alpha, image.mode)


def sharpen(image: Image.Image, amount: float = 1.5) -> Image.Image:
    """PIL 기반 선명도 향상. amount=1.0은 원본, 1.5~2.0 권장."""
    if amount < 0:
        raise ValueError("amount는 0 이상이어야 합니다.")
    return ImageEnhance.Sharpness(image).enhance(amount)


def upscale(image: Image.Image, scale: int = 2, model_path: str | None = None) -> Image.Image:
    """업스케일. cv2.dnn_superres 모델이 없으면 Lanczos 리사이즈로 폴백한다."""
    if scale not in (2, 3, 4):
        raise ValueError("scale은 2, 3, 4 중 하나여야 합니다.")

    if model_path and _CV2_AVAILABLE:
        try:
            bgr, alpha = _to_cv_bgr(image)
            sr = cv2.dnn_superres.DnnSuperResImpl_create()
            sr.readModel(model_path)
            sr.setModel("edsr", scale)
            upscaled = sr.upsample(bgr)
            if alpha is not None:
                new_size = (upscaled.shape[1], upscaled.shape[0])
                alpha_img = Image.fromarray(alpha).resize(new_size, Image.LANCZOS)
                alpha = np.array(alpha_img)
            return _to_pil(upscaled, alpha, image.mode)
        except Exception:  # noqa: BLE001
            logger.warning("업스케일 모델 로드 실패, Lanczos 폴백을 사용합니다.", exc_info=True)

    logger.info("업스케일 모델 미탑재, Lanczos 폴백 사용")
    width, height = image.size
    return image.resize((width * scale, height * scale), Image.LANCZOS)
