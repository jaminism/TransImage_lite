import pytest

from core.processors.printer import compute_print_size_mm, fit_to_page


def test_compute_print_size_mm():
    width_mm, height_mm = compute_print_size_mm((300, 300), source_dpi=300)
    assert round(width_mm, 1) == 25.4
    assert round(height_mm, 1) == 25.4


def test_compute_print_size_invalid_dpi():
    with pytest.raises(ValueError):
        compute_print_size_mm((100, 100), source_dpi=0)


def test_fit_to_page_landscape():
    width, height = fit_to_page((2000, 1000), (1000, 1000))
    assert width == 1000
    assert height == 500


def test_fit_to_page_invalid():
    with pytest.raises(ValueError):
        fit_to_page((0, 100), (100, 100))
