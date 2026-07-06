from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PIL import Image
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout

_SIZE_UNITS = ("B", "KB", "MB", "GB")


def format_file_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in _SIZE_UNITS:
        if size < 1024 or unit == _SIZE_UNITS[-1]:
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} {_SIZE_UNITS[-1]}"  # pragma: no cover


class ImageInfoPanel(QFrame):
    """참고 디자인(IMG_9186.png)의 우측 하단 "정보" 박스.

    어떤 편집 도구를 선택해도(속성 패널 QStackedWidget 전환과 무관하게) 항상 보이며,
    현재 열린 이미지의 파일명/해상도/파일 크기/생성일을 표시한다.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("infoCard")

        title = QLabel("정보")
        title.setObjectName("infoCardTitle")

        self._filename_value = QLabel("-")
        self._resolution_value = QLabel("-")
        self._size_value = QLabel("-")
        self._created_value = QLabel("-")
        for value_label in (
            self._filename_value,
            self._resolution_value,
            self._size_value,
            self._created_value,
        ):
            value_label.setObjectName("infoCardValue")
            value_label.setWordWrap(True)

        grid = QGridLayout()
        grid.setContentsMargins(0, 4, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(6)
        rows = (
            ("파일명", self._filename_value),
            ("해상도", self._resolution_value),
            ("크기", self._size_value),
            ("생성일", self._created_value),
        )
        for row, (label_text, value_label) in enumerate(rows):
            name_label = QLabel(label_text)
            name_label.setObjectName("infoCardLabel")
            grid.addWidget(name_label, row, 0)
            grid.addWidget(value_label, row, 1)
        grid.setColumnStretch(1, 1)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addLayout(grid)

    def set_info(self, path: str | None, image: Image.Image | None) -> None:
        if not path or image is None:
            self._filename_value.setText("-")
            self._filename_value.setToolTip("")
            self._resolution_value.setText("-")
            self._size_value.setText("-")
            self._created_value.setText("-")
            return

        file_path = Path(path)
        self._filename_value.setText(file_path.name)
        self._filename_value.setToolTip(path)
        self._resolution_value.setText(f"{image.width} x {image.height}")

        try:
            stat = file_path.stat()
        except OSError:
            self._size_value.setText("-")
            self._created_value.setText("-")
            return

        self._size_value.setText(format_file_size(stat.st_size))
        self._created_value.setText(datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M"))
