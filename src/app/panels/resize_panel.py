from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.processors.resize import PRESETS, resize_image, resize_to_preset


class ResizePanel(QWidget):
    """크기 조절 도구 패널. apply_requested(fn, kwargs, is_async)를 발생시킨다."""

    apply_requested = Signal(object, dict, bool)

    def __init__(self) -> None:
        super().__init__()

        self.preset_combo = QComboBox()
        self.preset_combo.addItem("직접 입력", None)
        for name in PRESETS:
            self.preset_combo.addItem(name, name)

        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 10000)
        self.width_spin.setValue(1080)

        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 10000)
        self.height_spin.setValue(1080)

        self.keep_ratio_check = QCheckBox("비율 고정")
        self.keep_ratio_check.setChecked(True)

        apply_btn = QPushButton("적용")
        apply_btn.setObjectName("primaryButton")
        apply_btn.clicked.connect(self._on_apply)

        form = QFormLayout()
        form.addRow("프리셋", self.preset_combo)
        form.addRow("너비(px)", self.width_spin)
        form.addRow("높이(px)", self.height_spin)
        form.addRow(self.keep_ratio_check)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>크기 조절</b>"))
        layout.addLayout(form)
        layout.addWidget(apply_btn)
        layout.addStretch(1)

    def _on_apply(self) -> None:
        preset = self.preset_combo.currentData()
        if preset:
            self.apply_requested.emit(resize_to_preset, {"preset_name": preset}, False)
        else:
            self.apply_requested.emit(
                resize_image,
                {
                    "width": self.width_spin.value(),
                    "height": self.height_spin.value(),
                    "keep_ratio": self.keep_ratio_check.isChecked(),
                },
                False,
            )
