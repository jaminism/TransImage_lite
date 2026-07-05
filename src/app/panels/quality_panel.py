from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from core.processors.quality import denoise, sharpen, upscale


class QualityPanel(QWidget):
    """품질 개선 도구 패널. 모든 처리는 시간이 걸릴 수 있어 비동기(is_async=True)로 요청한다."""

    apply_requested = Signal(object, dict, bool)

    def __init__(self) -> None:
        super().__init__()

        self.denoise_strength = QSlider(Qt.Horizontal)
        self.denoise_strength.setRange(1, 30)
        self.denoise_strength.setValue(10)
        denoise_btn = QPushButton("노이즈 제거")
        denoise_btn.clicked.connect(self._on_denoise)

        self.sharpen_amount = QSlider(Qt.Horizontal)
        self.sharpen_amount.setRange(100, 300)
        self.sharpen_amount.setValue(150)
        sharpen_btn = QPushButton("선명하게")
        sharpen_btn.clicked.connect(self._on_sharpen)

        self.upscale_combo = QComboBox()
        for factor in (2, 3, 4):
            self.upscale_combo.addItem(f"{factor}배", factor)
        upscale_btn = QPushButton("업스케일")
        upscale_btn.clicked.connect(self._on_upscale)

        form = QFormLayout()
        form.addRow("노이즈 제거 강도", self.denoise_strength)
        form.addRow(denoise_btn)
        form.addRow("선명도", self.sharpen_amount)
        form.addRow(sharpen_btn)
        form.addRow("업스케일 배율", self.upscale_combo)
        form.addRow(upscale_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>품질 개선</b>"))
        layout.addLayout(form)
        layout.addStretch(1)

    def _on_denoise(self) -> None:
        self.apply_requested.emit(denoise, {"strength": self.denoise_strength.value()}, True)

    def _on_sharpen(self) -> None:
        self.apply_requested.emit(sharpen, {"amount": self.sharpen_amount.value() / 100.0}, True)

    def _on_upscale(self) -> None:
        scale = self.upscale_combo.currentData()
        self.apply_requested.emit(upscale, {"scale": scale}, True)
