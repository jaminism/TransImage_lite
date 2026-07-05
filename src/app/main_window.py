from __future__ import annotations

from pathlib import Path

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QFileDialog,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QWidget,
)

from app.canvas_widget import CanvasWidget
from core.image_document import ImageDocument

TOOL_NAMES = ["리사이즈", "보정", "품질 개선", "텍스트", "배경 제거"]


class MainWindow(QMainWindow):
    """3단 레이아웃(툴 사이드바 / 캔버스 / 속성 패널) 뼈대.

    각 도구 패널의 실제 컨트롤과 처리 로직 연동은 ui-designer / imaging-engineer가
    다음 단계에서 구현한다. 현재는 이미지 열기/저장만 동작한다.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("TransImage Lite")
        self.resize(1280, 800)

        self.document = ImageDocument()
        self.canvas = CanvasWidget()

        self._build_layout()
        self._build_menu()

    def _build_layout(self) -> None:
        sidebar = QListWidget()
        sidebar.setFixedWidth(160)
        for name in TOOL_NAMES:
            QListWidgetItem(name, sidebar)
        sidebar.currentRowChanged.connect(self._on_tool_selected)

        self.properties_panel = QStackedWidget()
        for name in TOOL_NAMES:
            placeholder = QWidget()
            placeholder.setObjectName(name)
            self.properties_panel.addWidget(placeholder)
        self.properties_panel.setFixedWidth(300)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(sidebar)
        splitter.addWidget(self.canvas)
        splitter.addWidget(self.properties_panel)
        splitter.setStretchFactor(1, 1)

        self.setCentralWidget(splitter)

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("파일")

        open_action = QAction("열기...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self._open_image)
        file_menu.addAction(open_action)

        save_action = QAction("다른 이름으로 저장...", self)
        save_action.setShortcut(QKeySequence.SaveAs)
        save_action.triggered.connect(self._save_image_as)
        file_menu.addAction(save_action)

    def _on_tool_selected(self, index: int) -> None:
        if index >= 0:
            self.properties_panel.setCurrentIndex(index)

    def _open_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "이미지 열기",
            "",
            "이미지 파일 (*.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if not path:
            return
        try:
            image = Image.open(path)
            image.load()
            self.document.load(image)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "열기 실패", f"이미지를 열 수 없습니다:\n{exc}")
            return
        self.canvas.set_image(self.document.current)

    def _save_image_as(self) -> None:
        if self.document.current is None:
            QMessageBox.information(self, "저장", "저장할 이미지가 없습니다.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "다른 이름으로 저장",
            "",
            "PNG (*.png);;JPEG (*.jpg)",
        )
        if not path:
            return
        try:
            image = self.document.current
            if Path(path).suffix.lower() in (".jpg", ".jpeg") and image.mode == "RGBA":
                image = image.convert("RGB")
            image.save(path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "저장 실패", f"이미지를 저장할 수 없습니다:\n{exc}")
