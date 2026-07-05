from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.icons import icon
from core.processors.background_removal import remove_background, replace_background


class BackgroundPanel(QWidget):
    """배경 제거 도구 패널. 배경 제거는 무거운 연산이라 비동기(is_async=True)로 요청한다."""

    apply_requested = Signal(object, dict, bool)

    def __init__(self) -> None:
        super().__init__()

        self._fill_color = QColor(255, 255, 255)

        remove_btn = QPushButton(" 배경 제거 (투명화)")
        remove_btn.setIcon(icon("background_remove"))
        remove_btn.setObjectName("primaryButton")
        remove_btn.clicked.connect(self._on_remove)

        self.color_btn = QPushButton()
        self.color_btn.setIcon(icon("fill"))
        self._update_color_button()
        self.color_btn.clicked.connect(self._pick_color)

        fill_btn = QPushButton(" 단색 배경으로 채우기")
        fill_btn.setIcon(icon("fill"))
        fill_btn.clicked.connect(self._on_fill)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>배경 제거</b>"))
        layout.addWidget(QLabel("피사체만 남기고 배경을 투명하게 만듭니다."))
        layout.addWidget(remove_btn)
        layout.addWidget(QLabel("배경 제거 후 원하는 단색으로 채울 수 있습니다."))
        layout.addWidget(self.color_btn)
        layout.addWidget(fill_btn)
        layout.addStretch(1)

    def _update_color_button(self) -> None:
        self.color_btn.setStyleSheet(f"background-color: {self._fill_color.name()};")
        self.color_btn.setText(self._fill_color.name())

    def _pick_color(self) -> None:
        color = QColorDialog.getColor(self._fill_color, self, "배경 색상 선택")
        if color.isValid():
            self._fill_color = color
            self._update_color_button()

    def _on_remove(self) -> None:
        self.apply_requested.emit(remove_background, {}, True)

    def _on_fill(self) -> None:
        rgb = (self._fill_color.red(), self._fill_color.green(), self._fill_color.blue())
        self.apply_requested.emit(replace_background, {"background": rgb}, False)
