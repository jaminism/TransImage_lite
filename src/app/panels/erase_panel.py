from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFormLayout, QLabel, QSlider, QVBoxLayout, QWidget


class ErasePanel(QWidget):
    """지우개 도구 패널. 이 도구가 선택된 동안 캔버스에서 마우스 드래그로 지울 수 있다."""

    brush_size_changed = Signal(int)

    def __init__(self) -> None:
        super().__init__()

        self.brush_slider = QSlider(Qt.Horizontal)
        self.brush_slider.setRange(5, 100)
        self.brush_slider.setValue(24)
        self.brush_slider.valueChanged.connect(self.brush_size_changed.emit)

        form = QFormLayout()
        form.addRow("브러시 크기", self.brush_slider)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>지우개</b>"))
        layout.addWidget(QLabel("이 도구가 선택된 동안 캔버스를 마우스로 드래그하면 해당 부분이 지워집니다(투명 처리)."))
        layout.addLayout(form)
        layout.addStretch(1)

    @property
    def brush_radius(self) -> int:
        return self.brush_slider.value()
