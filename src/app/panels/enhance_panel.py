from __future__ import annotations

from PySide6.QtCore import QTimer, Signal, Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from app.icons import icon
from core.processors.enhance import apply_adjustments, apply_filter

_SLIDER_RANGE = (0, 200)  # 0~200 -> factor 0.0~2.0
_SLIDER_DEFAULT = 100  # factor 1.0


def _slider_to_factor(value: int) -> float:
    return value / 100.0


class EnhancePanel(QWidget):
    """보정 도구 패널. 슬라이더는 디바운스 미리보기, 버튼은 최종 적용/필터 프리셋.

    "초기화"는 슬라이더만 되돌리는 게 아니라, 이 패널에 들어왔을 때의 이미지 상태
    (reset_requested)로 실제로 되돌린다 — 적용을 이미 눌러 커밋된 조정도 함께 되돌아간다.
    """

    preview_requested = Signal(object, dict)
    apply_requested = Signal(object, dict, bool)
    reset_requested = Signal()

    def __init__(self) -> None:
        super().__init__()

        self.brightness_slider = self._make_slider()
        self.contrast_slider = self._make_slider()
        self.saturation_slider = self._make_slider()

        self._debounce = QTimer(singleShot=True)
        self._debounce.setInterval(150)
        self._debounce.timeout.connect(self._emit_preview)

        for slider in (self.brightness_slider, self.contrast_slider, self.saturation_slider):
            slider.valueChanged.connect(lambda _=None: self._debounce.start())

        form = QFormLayout()
        form.addRow("밝기", self.brightness_slider)
        form.addRow("대비", self.contrast_slider)
        form.addRow("채도", self.saturation_slider)

        apply_btn = QPushButton(" 적용")
        apply_btn.setIcon(icon("check"))
        apply_btn.setObjectName("primaryButton")
        apply_btn.clicked.connect(self._on_apply)

        reset_btn = QPushButton(" 초기화")
        reset_btn.setIcon(icon("refresh"))
        reset_btn.clicked.connect(self._on_reset)

        btn_row = QHBoxLayout()
        btn_row.addWidget(apply_btn)
        btn_row.addWidget(reset_btn)

        filter_row = QHBoxLayout()
        for label, preset in (("따뜻하게", "warm"), ("차갑게", "cool"), ("빈티지", "vintage"), ("흑백", "mono")):
            btn = QPushButton(label)
            btn.clicked.connect(lambda _=False, p=preset: self._on_filter(p))
            filter_row.addWidget(btn)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>보정</b>"))
        layout.addLayout(form)
        layout.addLayout(btn_row)
        layout.addWidget(QLabel("필터 프리셋"))
        layout.addLayout(filter_row)
        layout.addStretch(1)

    def _make_slider(self) -> QSlider:
        slider = QSlider(Qt.Horizontal)
        slider.setRange(*_SLIDER_RANGE)
        slider.setValue(_SLIDER_DEFAULT)
        return slider

    def _current_params(self) -> dict:
        return {
            "brightness": _slider_to_factor(self.brightness_slider.value()),
            "contrast": _slider_to_factor(self.contrast_slider.value()),
            "saturation": _slider_to_factor(self.saturation_slider.value()),
        }

    def _emit_preview(self) -> None:
        self.preview_requested.emit(apply_adjustments, self._current_params())

    def _on_apply(self) -> None:
        self.apply_requested.emit(apply_adjustments, self._current_params(), False)

    def _on_reset(self) -> None:
        self._debounce.stop()
        for slider in (self.brightness_slider, self.contrast_slider, self.saturation_slider):
            slider.blockSignals(True)
            slider.setValue(_SLIDER_DEFAULT)
            slider.blockSignals(False)
        self.reset_requested.emit()

    def _on_filter(self, preset_name: str) -> None:
        self.apply_requested.emit(apply_filter, {"preset_name": preset_name}, False)
