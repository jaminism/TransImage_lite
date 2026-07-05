from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QMenu, QPushButton, QSlider, QToolButton, QWidget

from app.icons import icon

_MIN_PERCENT = 10
_MAX_PERCENT = 400
_STEP_PERCENT = 10
_PRESETS = [25, 50, 75, 100, 150, 200, 300, 400]


class ZoomControl(QWidget):
    """상태바 우측의 확대/축소 컨트롤 (크롬의 %-지정 줌 UX를 참고).

    -/+ 버튼, 슬라이더, 프리셋 메뉴가 달린 %표시 버튼, "화면에 맞추기" 버튼으로
    구성된다. CanvasWidget과는 느슨하게 연결된다 — 이 위젯은 요청만 하고
    (zoom_percent_changed/fit_requested), 실제 반영 결과는 set_zoom_percent()로
    외부에서 다시 알려준다(캔버스의 Ctrl+휠 줌 등 다른 경로로 바뀐 값도 동기화).
    """

    zoom_percent_changed = Signal(float)
    fit_requested = Signal()

    def __init__(self) -> None:
        super().__init__()

        self._updating = False

        zoom_out_btn = QPushButton()
        zoom_out_btn.setIcon(icon("zoom_out"))
        zoom_out_btn.setFixedSize(28, 28)
        zoom_out_btn.setToolTip("축소")
        zoom_out_btn.clicked.connect(self._on_zoom_out)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(_MIN_PERCENT, _MAX_PERCENT)
        self.slider.setValue(100)
        self.slider.setFixedWidth(120)
        self.slider.setToolTip("확대/축소")
        self.slider.valueChanged.connect(self._on_slider_changed)

        zoom_in_btn = QPushButton()
        zoom_in_btn.setIcon(icon("zoom_in"))
        zoom_in_btn.setFixedSize(28, 28)
        zoom_in_btn.setToolTip("확대")
        zoom_in_btn.clicked.connect(self._on_zoom_in)

        self.percent_btn = QToolButton()
        self.percent_btn.setText("100%")
        self.percent_btn.setPopupMode(QToolButton.InstantPopup)
        self.percent_btn.setFixedWidth(60)
        self.percent_btn.setToolTip("배율 선택")

        menu = QMenu(self.percent_btn)
        for value in _PRESETS:
            action = menu.addAction(f"{value}%")
            action.triggered.connect(lambda _checked=False, v=value: self.set_zoom_percent(v, emit=True))
        menu.addSeparator()
        fit_action = menu.addAction("화면에 맞추기")
        fit_action.triggered.connect(self._on_fit_clicked)
        self.percent_btn.setMenu(menu)

        fit_btn = QPushButton()
        fit_btn.setIcon(icon("zoom_fit"))
        fit_btn.setFixedSize(28, 28)
        fit_btn.setToolTip("화면에 맞추기")
        fit_btn.clicked.connect(self._on_fit_clicked)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(6)
        layout.addWidget(zoom_out_btn)
        layout.addWidget(self.slider)
        layout.addWidget(zoom_in_btn)
        layout.addWidget(self.percent_btn)
        layout.addWidget(fit_btn)

    def set_zoom_percent(self, percent: float, emit: bool = False) -> None:
        """외부(캔버스)에서 실제 반영된 배율로 표시를 동기화한다. emit=True면
        직접 이 값을 요청하는 신호도 함께 보낸다(프리셋 메뉴 선택 등)."""
        percent = max(_MIN_PERCENT, min(_MAX_PERCENT, round(percent)))
        self._updating = True
        self.slider.setValue(int(percent))
        self.percent_btn.setText(f"{int(percent)}%")
        self._updating = False
        if emit:
            self.zoom_percent_changed.emit(float(percent))

    def _on_slider_changed(self, value: int) -> None:
        self.percent_btn.setText(f"{value}%")
        if not self._updating:
            self.zoom_percent_changed.emit(float(value))

    def _on_zoom_in(self) -> None:
        self.set_zoom_percent(self.slider.value() + _STEP_PERCENT, emit=True)

    def _on_zoom_out(self) -> None:
        self.set_zoom_percent(self.slider.value() - _STEP_PERCENT, emit=True)

    def _on_fit_clicked(self) -> None:
        self.fit_requested.emit()
