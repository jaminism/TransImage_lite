from __future__ import annotations


def compute_print_size_mm(image_px: tuple[int, int], source_dpi: int = 96) -> tuple[float, float]:
    """이미지 픽셀 크기를 주어진 DPI 기준 실제 인쇄 크기(mm)로 환산한다."""
    if source_dpi <= 0:
        raise ValueError("source_dpi는 0보다 커야 합니다.")
    width_px, height_px = image_px
    mm_per_inch = 25.4
    width_mm = width_px / source_dpi * mm_per_inch
    height_mm = height_px / source_dpi * mm_per_inch
    return width_mm, height_mm


def fit_to_page(image_size: tuple[int, int], page_size: tuple[int, int]) -> tuple[int, int]:
    """종횡비를 유지하며 페이지 크기에 맞춘 그리기 크기를 계산한다."""
    img_w, img_h = image_size
    page_w, page_h = page_size
    if img_w <= 0 or img_h <= 0 or page_w <= 0 or page_h <= 0:
        raise ValueError("크기 값은 0보다 커야 합니다.")
    scale = min(page_w / img_w, page_h / img_h)
    return round(img_w * scale), round(img_h * scale)
