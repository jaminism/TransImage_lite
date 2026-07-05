from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}


def open_image(path: str) -> Image.Image:
    """이미지를 열고 EXIF 회전을 반영한다. 지원하지 않는 포맷은 ValueError."""
    ext = Path(path).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"지원하지 않는 이미지 포맷입니다: {ext}")
    image = Image.open(path)
    image.load()
    return ImageOps.exif_transpose(image) or image


def save_image(image: Image.Image, path: str, quality: int = 90) -> None:
    """포맷에 맞춰 이미지를 저장한다. JPEG는 알파 채널을 흰 배경에 합성한다."""
    ext = Path(path).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"지원하지 않는 저장 포맷입니다: {ext}")

    if ext in (".jpg", ".jpeg") and image.mode in ("RGBA", "LA", "P"):
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.split()[-1])
        background.save(path, quality=quality, optimize=True)
    elif ext in (".jpg", ".jpeg"):
        image.convert("RGB").save(path, quality=quality, optimize=True)
    elif ext == ".webp":
        image.save(path, quality=quality, method=6)
    else:
        image.save(path, optimize=True)
