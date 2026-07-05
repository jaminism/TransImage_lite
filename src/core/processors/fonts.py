from __future__ import annotations

import os

_FONTS_DIR = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")


def resolve_windows_font_path(family_name: str) -> str | None:
    """Windows 레지스트리에서 설치된 폰트 family 이름으로 실제 폰트 파일 경로를 찾는다.

    PIL의 ImageFont.truetype()은 family 이름이 아니라 실제 파일 경로가 필요하므로,
    QFontComboBox 등에서 선택한 시스템 폰트 이름을 렌더링 가능한 경로로 변환한다.
    """
    try:
        import winreg
    except ImportError:  # pragma: no cover - Windows 전용
        return None

    key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
    except OSError:
        return None

    target = family_name.strip().lower()
    try:
        index = 0
        while True:
            try:
                value_name, value_data, _ = winreg.EnumValue(key, index)
            except OSError:
                break
            index += 1

            display_name = value_name.split(" (")[0]
            candidates = [display_name.lower()] + [p.strip().lower() for p in display_name.split("&")]
            if target in candidates:
                path = value_data if os.path.isabs(value_data) else os.path.join(_FONTS_DIR, value_data)
                if os.path.exists(path):
                    return path
        return None
    finally:
        winreg.CloseKey(key)
