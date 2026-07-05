from __future__ import annotations

from PIL import Image

ROTATE_LEFT = 90
ROTATE_RIGHT = -90


def rotate_image(image: Image.Image, angle: float, expand: bool = True) -> Image.Image:
    """이미지를 회전한다. angle은 시계 방향 각도(양수 = 시계 방향)."""
    return image.rotate(-angle, expand=expand, resample=Image.BICUBIC)


def flip_image(image: Image.Image, horizontal: bool = True) -> Image.Image:
    """좌우(horizontal=True) 또는 상하(horizontal=False) 반전."""
    transpose = Image.FLIP_LEFT_RIGHT if horizontal else Image.FLIP_TOP_BOTTOM
    return image.transpose(transpose)
