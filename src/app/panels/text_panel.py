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

from core.processors.text_overlay import add_text


class TextPanel(QWidget):
    """텍스트 추가 도구 패널."""

    apply_requested = Signal(object, dict, bool)

    def __init__(self) -> None:
        super().__init__()

        self._color = QColor(255, 255, 255)

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("텍스트 입력")

        self.size_spin = QSpinBox()
        self.size_spin.setRange(8, 300)
        self.size_spin.setValue(48)

        self.x_spin = QSpinBox()
        self.x_spin.setRange(0, 10000)
        self.x_spin.setValue(20)
        self.y_spin = QSpinBox()
        self.y_spin.setRange(0, 10000)
        self.y_spin.setValue(20)

        self.rotation_spin = QSpinBox()
        self.rotation_spin.setRange(-180, 180)
        self.rotation_spin.setValue(0)

        self.shadow_check = QCheckBox("그림자 효과")
        self.shadow_check.setChecked(True)

        self.color_btn = QPushButton()
        self._update_color_button()
        self.color_btn.clicked.connect(self._pick_color)

        apply_btn = QPushButton("적용")
        apply_btn.setObjectName("primaryButton")
        apply_btn.clicked.connect(self._on_apply)

        form = QFormLayout()
        form.addRow("텍스트", self.text_input)
        form.addRow("크기(px)", self.size_spin)
        form.addRow("X", self.x_spin)
        form.addRow("Y", self.y_spin)
        form.addRow("회전(도)", self.rotation_spin)
        form.addRow("색상", self.color_btn)
        form.addRow(self.shadow_check)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>텍스트 추가</b>"))
        layout.addLayout(form)
        layout.addWidget(apply_btn)
        layout.addStretch(1)

    def _update_color_button(self) -> None:
        self.color_btn.setStyleSheet(f"background-color: {self._color.name()};")
        self.color_btn.setText(self._color.name())

    def _pick_color(self) -> None:
        color = QColorDialog.getColor(self._color, self, "텍스트 색상 선택")
        if color.isValid():
            self._color = color
            self._update_color_button()

    def _on_apply(self) -> None:
        text = self.text_input.text().strip()
        if not text:
            return
        self.apply_requested.emit(
            add_text,
            {
                "text": text,
                "position": (self.x_spin.value(), self.y_spin.value()),
                "size": self.size_spin.value(),
                "color": (self._color.red(), self._color.green(), self._color.blue(), 255),
                "rotation": float(self.rotation_spin.value()),
                "shadow": self.shadow_check.isChecked(),
            },
            False,
        )
