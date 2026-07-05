from __future__ import annotations

from typing import Optional

from PIL import Image
from PIL.ImageQt import ImageQt
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPixmap, QWheelEvent
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsScene, QGraphicsView

_CANVAS_BACKGROUND = QColor("#151617")


class CanvasWidget(QGraphicsView):
    """이미지 표시/줌/팬을 담당하는 캔버스.

    실제 편집 로직은 포함하지 않는다 — core.processors가 반환한 이미지를
    set_image()로 전달받아 그리기만 담당한다.
    """

    def __init__(self) -> None:
        super().__init__()
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setFrameShape(QGraphicsView.NoFrame)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setBackgroundBrush(_CANVAS_BACKGROUND)

        self._pixmap_item: Optional[QGraphicsPixmapItem] = None

    def set_image(self, image: Optional[Image.Image]) -> None:
        self._scene.clear()
        self._pixmap_item = None
        if image is None:
            return
        qimage = ImageQt(image)
        pixmap = QPixmap.fromImage(qimage)
        self._pixmap_item = self._scene.addPixmap(pixmap)
        self._scene.setSceneRect(pixmap.rect())
        self.fitInView(self._pixmap_item, Qt.KeepAspectRatio)

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.modifiers() & Qt.ControlModifier:
            factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
            self.scale(factor, factor)
        else:
            super().wheelEvent(event)
