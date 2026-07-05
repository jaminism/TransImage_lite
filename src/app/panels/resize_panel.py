from __future__ import annotations

from PySide6.QtCore import QSize, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.icons import icon
from core.processors.resize import PRESETS, resize_image, resize_to_preset
from core.processors.transform import ROTATE_LEFT, ROTATE_RIGHT, flip_image, rotate_image

_ICON_SIZE = QSize(20, 20)


def _icon_button(icon_name: str, tooltip: str) -> QPushButton:
    btn = QPushButton()
    btn.setIcon(icon(icon_name))
    btn.setIconSize(_ICON_SIZE)
    btn.setToolTip(tooltip)
    btn.setFixedSize(40, 36)
    return btn


class ResizePanel(QWidget):
    """크기 조절 / 회전 / 뒤집기 도구 패널. apply_requested(fn, kwargs, is_async)를 발생시킨다."""

    apply_requested = Signal(object, dict, bool)
    angle_apply_requested = Signal(float)

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

        apply_btn = QPushButton(" 적용")
        apply_btn.setIcon(icon("check"))
        apply_btn.setObjectName("primaryButton")
        apply_btn.clicked.connect(self._on_apply_resize)

        form = QFormLayout()
        form.addRow("프리셋", self.preset_combo)
        form.addRow("너비(px)", self.width_spin)
        form.addRow("높이(px)", self.height_spin)
        form.addRow(self.keep_ratio_check)

        rotate_left_btn = _icon_button("rotate_left", "왼쪽으로 90도 회전")
        rotate_left_btn.clicked.connect(lambda: self._rotate(ROTATE_LEFT))

        rotate_right_btn = _icon_button("rotate_right", "오른쪽으로 90도 회전")
        rotate_right_btn.clicked.connect(lambda: self._rotate(ROTATE_RIGHT))

        flip_h_btn = _icon_button("flip_horizontal", "좌우 반전")
        flip_h_btn.clicked.connect(lambda: self._flip(horizontal=True))

        flip_v_btn = _icon_button("flip_vertical", "상하 반전")
        flip_v_btn.clicked.connect(lambda: self._flip(horizontal=False))

        rotate_row = QHBoxLayout()
        for btn in (rotate_left_btn, rotate_right_btn, flip_h_btn, flip_v_btn):
            rotate_row.addWidget(btn)
        rotate_row.addStretch(1)

        self.angle_spin = QSpinBox()
        self.angle_spin.setRange(-359, 359)
        self.angle_spin.setValue(0)
        self.angle_spin.setSuffix("°")
        self.angle_spin.setToolTip("시계 방향이 양수입니다")

        angle_apply_btn = QPushButton(" 각도 적용")
        angle_apply_btn.setIcon(icon("check"))
        angle_apply_btn.clicked.connect(self._on_apply_angle)

        angle_row = QHBoxLayout()
        angle_row.addWidget(self.angle_spin, stretch=1)
        angle_row.addWidget(angle_apply_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>크기 조절</b>"))
        layout.addLayout(form)
        layout.addWidget(apply_btn)
        layout.addSpacing(12)
        layout.addWidget(QLabel("<b>회전 / 뒤집기</b>"))
        layout.addLayout(rotate_row)
        layout.addWidget(QLabel("각도 직접 입력"))
        layout.addLayout(angle_row)
        layout.addStretch(1)

    def _on_apply_resize(self) -> None:
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

    def _rotate(self, angle: float) -> None:
        self.apply_requested.emit(rotate_image, {"angle": angle}, False)

    def _on_apply_angle(self) -> None:
        # 아이콘 회전(90도)과 달리, 각도 직접 입력은 "도구에 들어왔을 때(또는 마지막
        # 크기조절/아이콘 회전 시점) 이미지 기준 절대 각도"로 취급해야 한다. 그래야
        # 5도 적용 후 0도로 다시 적용하면 정확히 원래대로 돌아온다 — MainWindow가
        # 전용 신호로 baseline을 기준으로 재계산하도록 별도 신호를 쓴다.
        self.angle_apply_requested.emit(float(self.angle_spin.value()))

    def _flip(self, horizontal: bool) -> None:
        self.apply_requested.emit(flip_image, {"horizontal": horizontal}, False)
