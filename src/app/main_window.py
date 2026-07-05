from __future__ import annotations

import logging

from PIL import Image
from PIL.ImageQt import ImageQt
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence, QPainter, QPixmap
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QSplitter,
    QStackedWidget,
)

from app.canvas_widget import CanvasWidget
from app.panels.background_panel import BackgroundPanel
from app.panels.enhance_panel import EnhancePanel
from app.panels.export_panel import ExportPanel
from app.panels.quality_panel import QualityPanel
from app.panels.resize_panel import ResizePanel
from app.panels.text_panel import TextPanel
from core.image_document import ImageDocument
from core.processors.io import SUPPORTED_EXTENSIONS, open_image, save_image
from core.processors.printer import fit_to_page
from workers.async_tasks import ProcessWorker

logger = logging.getLogger(__name__)

TOOL_NAMES = ["리사이즈", "보정", "품질 개선", "텍스트", "배경 제거", "내보내기"]

_OPEN_FILTER = "이미지 파일 (*.png *.jpg *.jpeg *.bmp *.webp)"


class MainWindow(QMainWindow):
    """3단 레이아웃(툴 사이드바 / 캔버스 / 속성 패널)의 메인 윈도우.

    각 패널은 (processor_fn, kwargs, is_async) 형태로 apply_requested를 발생시키고,
    이 윈도우가 ImageDocument에 실제로 반영한다. 무거운 작업은 ProcessWorker로 비동기 실행한다.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("TransImage Lite")
        self.resize(1280, 800)

        self.document = ImageDocument()
        self.canvas = CanvasWidget()
        self._worker: ProcessWorker | None = None

        self._build_panels()
        self._build_layout()
        self._build_menu()
        self._build_status_bar()
        self._update_actions_enabled()

    # ------------------------------------------------------------------ UI 구성
    def _build_panels(self) -> None:
        self.resize_panel = ResizePanel()
        self.enhance_panel = EnhancePanel()
        self.quality_panel = QualityPanel()
        self.text_panel = TextPanel()
        self.background_panel = BackgroundPanel()
        self.export_panel = ExportPanel()

        self._panels = [
            self.resize_panel,
            self.enhance_panel,
            self.quality_panel,
            self.text_panel,
            self.background_panel,
            self.export_panel,
        ]

        for panel in self._panels:
            if hasattr(panel, "preview_requested"):
                panel.preview_requested.connect(self._on_preview_requested)
            if hasattr(panel, "apply_requested"):
                panel.apply_requested.connect(self._on_apply_requested)

        self.export_panel.save_requested.connect(self._on_save)
        self.export_panel.print_requested.connect(self._on_print)

    def _build_layout(self) -> None:
        sidebar = QListWidget()
        sidebar.setFixedWidth(160)
        for name in TOOL_NAMES:
            QListWidgetItem(name, sidebar)
        sidebar.setCurrentRow(0)
        sidebar.currentRowChanged.connect(self._on_tool_selected)
        self.sidebar = sidebar

        self.properties_panel = QStackedWidget()
        for panel in self._panels:
            self.properties_panel.addWidget(panel)
        self.properties_panel.setFixedWidth(320)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(sidebar)
        splitter.addWidget(self.canvas)
        splitter.addWidget(self.properties_panel)
        splitter.setStretchFactor(1, 1)

        self.setCentralWidget(splitter)

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("파일")

        self.open_action = QAction("열기...", self)
        self.open_action.setShortcut(QKeySequence.Open)
        self.open_action.triggered.connect(self._open_image)
        file_menu.addAction(self.open_action)

        self.save_action = QAction("다른 이름으로 저장...", self)
        self.save_action.setShortcut(QKeySequence.SaveAs)
        self.save_action.triggered.connect(lambda: self._on_save(90))
        file_menu.addAction(self.save_action)

        self.print_action = QAction("프린트...", self)
        self.print_action.setShortcut(QKeySequence.Print)
        self.print_action.triggered.connect(self._on_print)
        file_menu.addAction(self.print_action)

        edit_menu = self.menuBar().addMenu("편집")

        self.undo_action = QAction("실행 취소", self)
        self.undo_action.setShortcut(QKeySequence.Undo)
        self.undo_action.triggered.connect(self._on_undo)
        edit_menu.addAction(self.undo_action)

        self.redo_action = QAction("다시 실행", self)
        self.redo_action.setShortcut(QKeySequence.Redo)
        self.redo_action.triggered.connect(self._on_redo)
        edit_menu.addAction(self.redo_action)

    def _build_status_bar(self) -> None:
        self.status_progress = QProgressBar()
        self.status_progress.setRange(0, 0)
        self.status_progress.setMaximumWidth(160)
        self.status_progress.setVisible(False)
        self.statusBar().addPermanentWidget(self.status_progress)
        self.statusBar().showMessage("이미지를 열어주세요 (Ctrl+O)")

    # ------------------------------------------------------------------ 도구 선택
    def _on_tool_selected(self, index: int) -> None:
        if index >= 0:
            self.properties_panel.setCurrentIndex(index)
        self._refresh_canvas()

    # ------------------------------------------------------------------ 파일 열기
    def _open_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "이미지 열기", "", _OPEN_FILTER)
        if not path:
            return
        try:
            image = open_image(path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "열기 실패", f"이미지를 열 수 없습니다:\n{exc}")
            return
        self.document.load(image)
        self._refresh_canvas()
        self._update_actions_enabled()
        self.statusBar().showMessage(f"열림: {path} ({image.width}x{image.height})")

    # ------------------------------------------------------------------ 미리보기 / 적용
    def _on_preview_requested(self, fn, kwargs: dict) -> None:
        if self.document.current is None:
            return
        try:
            preview = fn(self.document.current, **kwargs)
        except Exception:  # noqa: BLE001
            logger.debug("미리보기 계산 실패", exc_info=True)
            return
        self.canvas.set_image(preview)

    def _on_apply_requested(self, fn, kwargs: dict, is_async: bool) -> None:
        if self.document.current is None:
            QMessageBox.information(self, "알림", "먼저 이미지를 열어주세요.")
            return

        if is_async:
            self._run_async(fn, kwargs)
            return

        try:
            self.document.apply(fn, **kwargs)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "처리 실패", str(exc))
            return
        self._refresh_canvas()
        self._update_actions_enabled()

    def _run_async(self, fn, kwargs: dict) -> None:
        image = self.document.current
        self._set_busy(True)

        worker = ProcessWorker(fn, image=image, **kwargs)
        self._worker = worker  # GC 방지를 위해 참조 유지

        def on_ok(result: Image.Image) -> None:
            self._set_busy(False)
            try:
                self.document.apply_result(result)
            except Exception as exc:  # noqa: BLE001
                QMessageBox.critical(self, "처리 실패", str(exc))
                return
            self._refresh_canvas()
            self._update_actions_enabled()

        def on_fail(message: str) -> None:
            self._set_busy(False)
            QMessageBox.critical(self, "처리 실패", message)

        worker.finished_ok.connect(on_ok)
        worker.failed.connect(on_fail)
        worker.start()

    def _set_busy(self, busy: bool) -> None:
        self.sidebar.setEnabled(not busy)
        self.properties_panel.setEnabled(not busy)
        self.status_progress.setVisible(busy)
        self.statusBar().showMessage("처리 중..." if busy else "완료")

    # ------------------------------------------------------------------ Undo/Redo
    def _on_undo(self) -> None:
        self.document.undo()
        self._refresh_canvas()
        self._update_actions_enabled()

    def _on_redo(self) -> None:
        self.document.redo()
        self._refresh_canvas()
        self._update_actions_enabled()

    def _update_actions_enabled(self) -> None:
        has_image = self.document.current is not None
        self.save_action.setEnabled(has_image)
        self.print_action.setEnabled(has_image)
        self.undo_action.setEnabled(self.document.can_undo())
        self.redo_action.setEnabled(self.document.can_redo())

    # ------------------------------------------------------------------ 저장 / 프린트
    def _on_save(self, quality: int) -> None:
        if self.document.current is None:
            QMessageBox.information(self, "저장", "저장할 이미지가 없습니다.")
            return
        filters = "PNG (*.png);;JPEG (*.jpg);;WEBP (*.webp);;BMP (*.bmp)"
        path, _ = QFileDialog.getSaveFileName(self, "다른 이름으로 저장", "", filters)
        if not path:
            return
        try:
            save_image(self.document.current, path, quality=quality)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "저장 실패", f"이미지를 저장할 수 없습니다:\n{exc}")
            return
        self.statusBar().showMessage(f"저장됨: {path}")

    def _on_print(self) -> None:
        if self.document.current is None:
            QMessageBox.information(self, "프린트", "출력할 이미지가 없습니다.")
            return

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        image = self.document.current.convert("RGB")
        qimage = ImageQt(image)
        pixmap = QPixmap.fromImage(qimage)

        painter = QPainter(printer)
        try:
            page_rect = printer.pageRect(QPrinter.Unit.DevicePixel)
            draw_w, draw_h = fit_to_page(
                (pixmap.width(), pixmap.height()),
                (int(page_rect.width()), int(page_rect.height())),
            )
            painter.drawPixmap(0, 0, draw_w, draw_h, pixmap)
        finally:
            painter.end()

    # ------------------------------------------------------------------ 캔버스 갱신
    def _refresh_canvas(self) -> None:
        self.canvas.set_image(self.document.current)


__all__ = ["MainWindow", "TOOL_NAMES", "SUPPORTED_EXTENSIONS"]
