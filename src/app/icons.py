from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

_ICONS_DIR = Path(__file__).parent.parent / "resources" / "icons"


def _rasterize(path: Path, size: int) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    renderer = QSvgRenderer(str(path))
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return pixmap


@lru_cache(maxsize=None)
def icon(name: str) -> QIcon:
    """src/resources/icons/{name}.svg 를 QSvgRenderer로 직접 래스터화해 QIcon으로 반환한다 (캐시됨).

    QPixmap(path)/QIcon(path) 기반 로딩은 이 환경에서 Qt의 svg 이미지 플러그인이
    등록되지 않아 항상 null을 반환하므로, QSvgRenderer + QPainter로 직접 그린다.
    """
    path = _ICONS_DIR / f"{name}.svg"
    result = QIcon()
    for size in (16, 20, 24, 32, 48):
        result.addPixmap(_rasterize(path, size))
    return result
