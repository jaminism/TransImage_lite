from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.icons import icon
from core.processors.text_overlay import add_text


class TextPanel(QWidget):
    """텍스트 추가 도구 패널.

    입력한 텍스트는 캔버스 위에 움직일 수 있는 오버레이로 미리 보여주고(overlay_changed),
    사용자가 마우스로 원하는 위치에 드래그한 뒤 "적용"을 누르면 그 위치에 실제로
    합성한다(text_apply_requested) — 최종 위치는 캔버스가 갖고 있으므로 여기서는 넘기지 않는다.
    """

    overlay_changed = Signal(dict)
    text_apply_requested = Signal(dict)

    def __init__(self) -> None:
        super().__init__()

        self._color = QColor(255, 255, 255)

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("텍스트 입력")
        self.text_input.textChanged.connect(self._emit_overlay_changed)

        self.size_spin = QSpinBox()
        self.size_spin.setRange(8, 300)
        self.size_spin.setValue(48)
        self.size_spin.valueChanged.connect(self._emit_overlay_changed)

        self.rotation_spin = QSpinBox()
        self.rotation_spin.setRange(-180, 180)
        self.rotation_spin.setValue(0)
        self.rotation_spin.valueChanged.connect(self._emit_overlay_changed)

        self.shadow_check = QCheckBox("그림자 효과")
        self.shadow_check.setChecked(True)

        self.color_btn = QPushButton()
        self.color_btn.setIcon(icon("fill"))
        self._update_color_button()
        self.color_btn.clicked.connect(self._pick_color)

        apply_btn = QPushButton(" 적용 (드래그한 위치에 합성)")
        apply_btn.setIcon(icon("check"))
        apply_btn.setObjectName("primaryButton")
        apply_btn.clicked.connect(self._on_apply)

        form = QFormLayout()
        form.addRow("텍스트", self.text_input)
        form.addRow("크기(px)", self.size_spin)
        form.addRow("회전(도)", self.rotation_spin)
        form.addRow("색상", self.color_btn)
        form.addRow(self.shadow_check)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>텍스트 추가</b>"))
        layout.addWidget(QLabel("캔버스에 표시된 텍스트를 마우스로 드래그해 위치를 정하세요."))
        layout.addLayout(form)
        layout.addWidget(apply_btn)
        layout.addStretch(1)

    def emit_current_overlay(self) -> None:
        """텍스트 도구로 전환될 때 현재 입력값 기준으로 오버레이를 다시 표시한다."""
        self._emit_overlay_changed()

    def current_params(self) -> dict:
        return {
            "text": self.text_input.text(),
            "size": self.size_spin.value(),
            "color": (self._color.red(), self._color.green(), self._color.blue(), 255),
            "rotation": float(self.rotation_spin.value()),
        }

    def _emit_overlay_changed(self, *_args) -> None:
        self.overlay_changed.emit(self.current_params())

    def _update_color_button(self) -> None:
        self.color_btn.setStyleSheet(f"background-color: {self._color.name()};")
        self.color_btn.setText(self._color.name())

    def _pick_color(self) -> None:
        color = QColorDialog.getColor(self._color, self, "텍스트 색상 선택")
        if color.isValid():
            self._color = color
            self._update_color_button()
            self._emit_overlay_changed()

    def _on_apply(self) -> None:
        text = self.text_input.text().strip()
        if not text:
            return
        params = self.current_params()
        params["shadow"] = self.shadow_check.isChecked()
        self.text_apply_requested.emit(params)
