from __future__ import annotations

from typing import Optional

from PIL import Image, ImageDraw
from PIL.ImageQt import ImageQt
from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QMouseEvent, QPainter, QPixmap, QWheelEvent
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

_CANVAS_BACKGROUND = QColor("#151617")


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
    """이미지 표시/줌/팬/텍스트 드래그/지우개를 담당하는 캔버스.

    실제 편집 로직(픽셀 계산)은 포함하지 않는다 — core.processors가 반환한 이미지를
    set_image()로 전달받아 그리기만 담당한다. 단, 지우개 모드는 실시간 상호작용이
    필요해 알파 채널을 직접 다듬는 최소한의 로직만 예외적으로 갖는다.
    """

    erase_stroke_finished = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setFrameShape(QGraphicsView.NoFrame)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setBackgroundBrush(_CANVAS_BACKGROUND)

        self._pixmap_item: Optional[QGraphicsPixmapItem] = None
        self._text_item: Optional[QGraphicsSimpleTextItem] = None

        self._erase_mode = False
        self._erasing = False
        self._brush_radius = 24
        self._erase_source: Optional[Image.Image] = None  # 원본 해상도 (스트로크 종료 시에만 갱신)
        self._erase_preview: Optional[Image.Image] = None  # 화면 표시용 축소 프록시 (드래그 중 실시간 편집)
        self._erase_scale = 1.0  # preview_size = source_size * scale
        self._stroke_points: list[tuple[float, float, float]] = []  # (원본 좌표 x, y, 반지름)

        self._busy_overlay = _BusyOverlay(self)

    # ------------------------------------------------------------------ 이미지 표시
    def set_image(self, image: Optional[Image.Image]) -> None:
        self._scene.clear()
        self._pixmap_item = None
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
        if self._text_item is None:
            self._text_item = QGraphicsSimpleTextItem()
            self._text_item.setFlag(QGraphicsItem.ItemIsMovable, True)
            self._text_item.setFlag(QGraphicsItem.ItemIsSelectable, True)
            self._text_item.setZValue(10)
            rect = self._pixmap_item.boundingRect()
            self._text_item.setPos(QPointF(rect.width() / 2 - 40, rect.height() / 2 - size / 2))
            self._scene.addItem(self._text_item)

        self._text_item.setText(text if text else " ")
        font = QFont(font_family or "Arial")
        font.setPixelSize(max(6, size))
        self._text_item.setFont(font)
        self._text_item.setBrush(QColor(color[0], color[1], color[2]))
        self._text_item.setRotation(rotation)

    def get_text_overlay_position(self) -> tuple[int, int]:
        if self._text_item is None:
            return (20, 20)
        pos = self._text_item.pos()
        return (int(pos.x()), int(pos.y()))

    def clear_text_overlay(self) -> None:
        if self._text_item is not None:
            self._scene.removeItem(self._text_item)
            self._text_item = None

    # ------------------------------------------------------------------ 지우개
    #
    # 고해상도 사진(수천만 픽셀)을 마우스 이동마다 그대로 QImage로 변환하면 변환 1회에
    # 수백MB가 필요해 MemoryError가 난다. 그래서 화면 표시는 축소된 프록시 이미지에서만
    # 실시간으로 지우고, 실제 원본 해상도 반영은 스트로크가 끝났을 때(마우스 뗄 때) 딱
    # 한 번만 수행한다.
    _PREVIEW_MAX_DIM = 1600

    def begin_erase(self, image: Image.Image, brush_radius: int) -> None:
        self._erase_mode = True
        self._brush_radius = brush_radius
        self._erase_source = image.convert("RGBA")
        self._stroke_points = []

        max_dim = max(self._erase_source.size)
        self._erase_scale = min(1.0, self._PREVIEW_MAX_DIM / max_dim) if max_dim > 0 else 1.0
        if self._erase_scale < 1.0:
            preview_size = (
                max(1, round(self._erase_source.width * self._erase_scale)),
                max(1, round(self._erase_source.height * self._erase_scale)),
            )
            self._erase_preview = self._erase_source.resize(preview_size, Image.BILINEAR)
        else:
            self._erase_preview = self._erase_source.copy()

        self.setDragMode(QGraphicsView.NoDrag)
        self._refresh_erase_pixmap()
        if self._pixmap_item is not None:
            # 프록시 크기가 원본과 다를 수 있으므로 sceneRect에 맞춰 뷰를 다시 맞춘다.
            # (안 하면 mapToScene() 좌표가 이전 sceneRect 기준으로 어긋난다.)
            self.fitInView(self._pixmap_item, Qt.KeepAspectRatio)

    def end_erase(self) -> None:
        self._erase_mode = False
        self._erasing = False
        self._erase_source = None
        self._erase_preview = None
        self._stroke_points = []
        self.setDragMode(QGraphicsView.ScrollHandDrag)

    def set_brush_radius(self, radius: int) -> None:
        self._brush_radius = radius

    def _refresh_erase_pixmap(self) -> None:
        if self._erase_preview is None:
            return
        qimage = ImageQt(self._erase_preview)
        pixmap = QPixmap.fromImage(qimage)
        if self._pixmap_item is None:
            self._pixmap_item = self._scene.addPixmap(pixmap)
        else:
            self._pixmap_item.setPixmap(pixmap)
        # 프록시 크기가 원본 이미지 크기와 다르므로 mapToScene() 좌표가 프록시 픽셀
        # 좌표와 일치하도록 매번 sceneRect를 프록시 크기에 맞춘다.
        self._scene.setSceneRect(pixmap.rect())

    def _erase_at(self, view_pos) -> None:
        if self._erase_preview is None:
            return
        scene_pos = self.mapToScene(view_pos)
        x, y = scene_pos.x(), scene_pos.y()
        r_preview = max(1.0, self._brush_radius * self._erase_scale)

        draw = ImageDraw.Draw(self._erase_preview)
        draw.ellipse((x - r_preview, y - r_preview, x + r_preview, y + r_preview), fill=(0, 0, 0, 0))
        self._refresh_erase_pixmap()

        self._stroke_points.append((x / self._erase_scale, y / self._erase_scale, float(self._brush_radius)))

    def _commit_erase_stroke(self) -> None:
        if not self._stroke_points or self._erase_source is None:
            return
        result = self._erase_source.copy()
        draw = ImageDraw.Draw(result)
        for sx, sy, sr in self._stroke_points:
            draw.ellipse((sx - sr, sy - sr, sx + sr, sy + sr), fill=(0, 0, 0, 0))
        self._erase_source = result
        self._stroke_points = []
        self.erase_stroke_finished.emit(result.copy())

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self._erase_mode and event.button() == Qt.LeftButton and self._erase_preview is not None:
            self._erasing = True
            self._erase_at(event.position().toPoint())
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._erase_mode and self._erasing:
            self._erase_at(event.position().toPoint())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self._erase_mode and self._erasing:
            self._erasing = False
            self._commit_erase_stroke()
            event.accept()
            return
        super().mouseReleaseEvent(event)
