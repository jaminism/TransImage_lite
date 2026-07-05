from __future__ import annotations

from typing import Optional

from PIL import Image
from PIL.ImageQt import ImageQt
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap, QWheelEvent
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

_CANVAS_BACKGROUND = QColor("#151617")
_TEXT_PADDING = 8
_HANDLE_BORDER = QColor("#7c5cff")
_HANDLE_FILL = QColor(124, 92, 255, 40)


class _BusyOverlay(QWidget):
    """비동기 처리 중임을 시각적으로 알리는 반투명 오버레이(스피너 + 문구)."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            "_BusyOverlay { background-color: rgba(10, 8, 16, 175); border-radius: 0px; }"
        )
        self._label = QLabel("처리 중...")
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: 600; background: transparent;")

        self._bar = QProgressBar()
        self._bar.setRange(0, 0)
        self._bar.setFixedWidth(220)
        self._bar.setTextVisible(False)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._label, alignment=Qt.AlignHCenter)
        layout.addSpacing(10)
        layout.addWidget(self._bar, alignment=Qt.AlignHCenter)
        self.hide()

    def set_message(self, text: str) -> None:
        self._label.setText(text)


class CanvasWidget(QGraphicsView):
    """이미지 표시/줌/팬/텍스트 드래그를 담당하는 캔버스.

    실제 편집 로직(픽셀 계산)은 포함하지 않는다 — core.processors가 반환한 이미지를
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
        self._text_handle: Optional[QGraphicsRectItem] = None
        self._text_item: Optional[QGraphicsSimpleTextItem] = None

        self._busy_overlay = _BusyOverlay(self)

    # ------------------------------------------------------------------ 이미지 표시
    def set_image(self, image: Optional[Image.Image]) -> None:
        self._scene.clear()
        self._pixmap_item = None
        self._text_handle = None
        self._text_item = None
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

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._busy_overlay.setGeometry(self.rect())

    # ------------------------------------------------------------------ 진행 중 표시
    def set_busy(self, busy: bool, message: str = "처리 중...") -> None:
        if busy:
            self._busy_overlay.set_message(message)
            self._busy_overlay.setGeometry(self.rect())
            self._busy_overlay.show()
            self._busy_overlay.raise_()
        else:
            self._busy_overlay.hide()

    # ------------------------------------------------------------------ 텍스트 드래그 오버레이
    #
    # 텍스트 자체(QGraphicsSimpleTextItem)를 직접 드래그 대상으로 삼으면, 글자가 짧거나
    # 확대 배율이 낮을 때 실제 글리프 모양 밖을 클릭하면 드래그가 안 잡히는 문제가 있다.
    # 그래서 여유 있는 패딩을 가진 사각형(_text_handle)을 실제 드래그 대상으로 두고,
    # 텍스트는 그 안에 표시만 되는 자식 아이템으로 붙인다 — 항상 넉넉하고 일관된
    # 히트박스를 보장한다.
    def show_text_overlay(
        self,
        text: str,
        size: int = 48,
        color: tuple[int, int, int, int] = (255, 255, 255, 255),
        rotation: float = 0.0,
        font_family: str = "Arial",
    ) -> None:
        if self._pixmap_item is None:
            return
        if self._text_handle is None:
            self._text_handle = QGraphicsRectItem()
            self._text_handle.setFlag(QGraphicsItem.ItemIsMovable, True)
            self._text_handle.setFlag(QGraphicsItem.ItemIsSelectable, True)
            self._text_handle.setZValue(10)
            self._text_handle.setPen(_HANDLE_BORDER)
            self._text_handle.setBrush(_HANDLE_FILL)
            rect = self._pixmap_item.boundingRect()
            self._text_handle.setPos(QPointF(rect.width() / 2 - 40, rect.height() / 2 - size / 2))
            self._scene.addItem(self._text_handle)

            self._text_item = QGraphicsSimpleTextItem(self._text_handle)
            self._text_item.setAcceptedMouseButtons(Qt.NoButton)

        self._text_item.setText(text if text else " ")
        font = QFont(font_family or "Arial")
        font.setPixelSize(max(6, size))
        self._text_item.setFont(font)
        self._text_item.setBrush(QColor(color[0], color[1], color[2]))
        self._text_item.setPos(_TEXT_PADDING, _TEXT_PADDING)

        text_rect = self._text_item.boundingRect()
        self._text_handle.setRect(0, 0, text_rect.width() + _TEXT_PADDING * 2, text_rect.height() + _TEXT_PADDING * 2)
        self._text_handle.setTransformOriginPoint(self._text_handle.rect().center())
        self._text_handle.setRotation(rotation)

    def get_text_overlay_position(self) -> tuple[int, int]:
        if self._text_handle is None:
            return (20, 20)
        pos = self._text_handle.pos()
        return (int(pos.x()) + _TEXT_PADDING, int(pos.y()) + _TEXT_PADDING)

    def clear_text_overlay(self) -> None:
        if self._text_handle is not None:
            self._scene.removeItem(self._text_handle)  # 자식인 _text_item도 함께 제거됨
            self._text_handle = None
            self._text_item = None
