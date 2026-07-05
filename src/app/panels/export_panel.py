from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFormLayout, QLabel, QPushButton, QSlider, QVBoxLayout, QWidget


class ExportPanel(QWidget):
    """저장/프린트 도구 패널. 실제 파일 대화상자와 프린트 다이얼로그는 MainWindow가 담당한다."""

    save_requested = Signal(int)
    print_requested = Signal()

    def __init__(self) -> None:
        super().__init__()

        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(90)

        save_btn = QPushButton("다른 이름으로 저장...")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(lambda: self.save_requested.emit(self.quality_slider.value()))

        print_btn = QPushButton("프린트...")
        print_btn.clicked.connect(self.print_requested.emit)

        form = QFormLayout()
        form.addRow("JPEG/WEBP 품질", self.quality_slider)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>내보내기</b>"))
        layout.addLayout(form)
        layout.addWidget(save_btn)
        layout.addWidget(print_btn)
        layout.addStretch(1)
