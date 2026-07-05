import sys

import pytest

from core.processors.fonts import resolve_windows_font_path


@pytest.mark.skipif(sys.platform != "win32", reason="Windows 전용 레지스트리 조회")
def test_resolve_arial_finds_a_real_file():
    path = resolve_windows_font_path("Arial")
    assert path is not None
    import os

    assert os.path.exists(path)


def test_resolve_unknown_family_returns_none():
    assert resolve_windows_font_path("Definitely Not A Real Font XYZ123") is None
