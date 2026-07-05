from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor, QFont, QFontDatabase
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QFileDialog,
    QFontComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.icons import icon
from core.processors.fonts import resolve_windows_font_path
from core.processors.text_overlay import add_text


class TextPanel(QWidget):
    """텍스트 추가 도구 패널.

    입력한 텍스트는 캔버스 위에 움직일 수 있는 오버레이로 미리 보여주고(overlay_changed),
    사용자가 마우스로 원하는 위치에 드래그한 뒤 "적용"을 누르면 그 위치에 실제로
    합성한다(text_apply_requested) — 최종 위치는 캔버스가 갖고 있으므로 여기서는 넘기지 않는다.
    """

    overlay_changed = Signal(dict)
    text_apply_requested = Signal(dict)
    reset_requested = Signal()

    def __init__(self) -> None:
        super().__init__()

        self._color = QColor(255, 255, 255)
        self._custom_fonts: dict[str, str] = {}  # family 이름 -> 사용자가 추가한 폰트 파일 경로

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("텍스트 입력")
        self.text_input.textChanged.connect(self._emit_overlay_changed)

        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont("Arial"))
        self.font_combo.currentFontChanged.connect(self._emit_overlay_changed)

        add_font_btn = QPushButton(" 폰트 추가...")
        add_font_btn.setToolTip("내 컴퓨터의 폰트 파일(.ttf/.otf)을 추가합니다")
        add_font_btn.clicked.connect(self._on_add_font)

        self.size_spin = QSpinBox()
        self.size_spin.setRange(1, 30)
        self.size_spin.setValue(6)
        self.size_spin.setSuffix("%")
        self.size_spin.setToolTip("이미지 높이 대비 텍스트 크기 비율 — 해상도가 달라져도 항상 같은 비율로 보입니다")
        self.size_spin.setMinimumWidth(90)
        self.size_spin.valueChanged.connect(self._emit_overlay_changed)

        self.rotation_spin = QSpinBox()
        self.rotation_spin.setRange(-180, 180)
        self.rotation_spin.setValue(0)
        self.rotation_spin.setMinimumWidth(90)
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
        apply_btn.setMinimumHeight(36)
        apply_btn.clicked.connect(self._on_apply)

        reset_btn = QPushButton(" 초기화")
        reset_btn.setIcon(icon("refresh"))
        reset_btn.setToolTip("텍스트/크기/회전/색상/폰트를 기본값으로 되돌리고 미리보기를 지웁니다")
        reset_btn.clicked.connect(self._on_reset)

        form = QFormLayout()
        form.addRow("텍스트", self.text_input)
        form.addRow("폰트", self.font_combo)
        form.addRow("", add_font_btn)
        form.addRow("크기(이미지 높이 대비)", self.size_spin)
        form.addRow("회전(도)", self.rotation_spin)
        form.addRow("색상", self.color_btn)
        form.addRow(self.shadow_check)

        btn_row = QHBoxLayout()
        btn_row.addWidget(apply_btn, stretch=1)
        btn_row.addWidget(reset_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>텍스트 추가</b>"))
        layout.addWidget(QLabel("캔버스에 표시된 텍스트를 마우스로 드래그해 위치를 정하세요."))
        layout.addLayout(form)
        layout.addLayout(btn_row)
        layout.addStretch(1)

    def emit_current_overlay(self) -> None:
        """텍스트 도구로 전환될 때 현재 입력값 기준으로 오버레이를 다시 표시한다."""
        self._emit_overlay_changed()

    def current_params(self) -> dict:
        family = self.font_combo.currentFont().family()
        return {
            "text": self.text_input.text(),
            "size_percent": self.size_spin.value(),
            "color": (self._color.red(), self._color.green(), self._color.blue(), 255),
            "rotation": float(self.rotation_spin.value()),
            "font_family": family,
            "font_path": self._resolve_font_path(family),
        }

    def _resolve_font_path(self, family: str) -> str | None:
        if family in self._custom_fonts:
            return self._custom_fonts[family]
        return resolve_windows_font_path(family)

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

    def _on_add_font(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "폰트 파일 추가", "", "폰트 파일 (*.ttf *.otf *.ttc)")
        if not path:
            return
        font_id = QFontDatabase.addApplicationFont(path)
        families = QFontDatabase.applicationFontFamilies(font_id) if font_id != -1 else []
        if not families:
            QMessageBox.warning(self, "폰트 추가 실패", "폰트 파일을 불러올 수 없습니다.")
            return
        family = families[0]
        self._custom_fonts[family] = path
        self.font_combo.setCurrentFont(QFont(family))
        self._emit_overlay_changed()

    def _on_apply(self) -> None:
        # 빈 텍스트라도 신호는 항상 보낸다 — MainWindow가 사용자에게 명확한 안내를 띄운다.
        # (여기서 조용히 무시하면 사용자 입장에서는 "적용 버튼이 안 먹는다"로 보인다.)
        params = self.current_params()
        params["shadow"] = self.shadow_check.isChecked()
        self.text_apply_requested.emit(params)

    def _on_reset(self) -> None:
        self.text_input.blockSignals(True)
        self.text_input.clear()
        self.text_input.blockSignals(False)

        self.font_combo.blockSignals(True)
        self.font_combo.setCurrentFont(QFont("Arial"))
        self.font_combo.blockSignals(False)

        self.size_spin.blockSignals(True)
        self.size_spin.setValue(6)
        self.size_spin.blockSignals(False)

        self.rotation_spin.blockSignals(True)
        self.rotation_spin.setValue(0)
        self.rotation_spin.blockSignals(False)

        self._color = QColor(255, 255, 255)
        self._update_color_button()
        self.shadow_check.setChecked(True)

        self.reset_requested.emit()
