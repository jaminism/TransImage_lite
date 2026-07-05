from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.icons import icon

_CARD_SPECS = [
    ("open", "사진 가져오기", "사진을 불러와 편집을 시작하세요", "open"),
    ("enhance", "빠른 보정", "밝기/대비/필터로 빠르게 편집", "enhance"),
    ("text", "글씨 추가", "다양한 글꼴로 글씨를 넣으세요", "text"),
    ("background_remove", "배경 제거", "피사체만 남기고 배경을 지워요", "background"),
]


class _QuickActionCard(QPushButton):
    def __init__(self, icon_name: str, title: str, subtitle: str) -> None:
        super().__init__()
        self.setObjectName("quickActionCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumSize(140, 120)

        icon_label = QLabel()
        icon_label.setPixmap(icon(icon_name).pixmap(32, 32))
        icon_label.setAlignment(Qt.AlignCenter)

        title_label = QLabel(f"<b>{title}</b>")
        title_label.setAlignment(Qt.AlignCenter)

        subtitle_label = QLabel(subtitle)
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setWordWrap(True)
        subtitle_label.setStyleSheet("color: #a8abb4; font-size: 11px;")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)


class _RecentFileCard(QPushButton):
    def __init__(self, path: str) -> None:
        super().__init__()
        self.path = path
        self.setObjectName("recentFileCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(140, 120)

        from PySide6.QtGui import QPixmap

        thumb = QLabel()
        thumb.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            thumb.setPixmap(pixmap.scaled(120, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        name_label = QLabel(Path(path).name)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setStyleSheet("font-size: 11px;")

        layout = QVBoxLayout(self)
        layout.addWidget(thumb)
        layout.addWidget(name_label)


class HomeWidget(QWidget):
    """이미지가 열려있지 않을 때 보여주는 홈 화면.

    환영 문구 + 주요 기능 바로가기 카드 + 최근 작업 목록으로 구성된다.
    """

    open_requested = Signal()
    quick_action_requested = Signal(str)  # "enhance" | "text" | "background"
    recent_file_opened = Signal(str)

    def __init__(self) -> None:
        super().__init__()

        title = QLabel("안녕하세요! \U0001F44B")
        title.setStyleSheet("font-size: 22px; font-weight: 700;")

        subtitle = QLabel("Trans Pro에 오신 것을 환영합니다.")
        subtitle.setStyleSheet("color: #a8abb4; font-size: 13px;")

        cards_layout = QGridLayout()
        cards_layout.setSpacing(12)
        for col, (icon_name, title_text, subtitle_text, action) in enumerate(_CARD_SPECS):
            card = _QuickActionCard(icon_name, title_text, subtitle_text)
            card.clicked.connect(lambda _checked=False, a=action: self._on_card_clicked(a))
            cards_layout.addWidget(card, 0, col)

        self._recent_row = QHBoxLayout()
        self._recent_row.setSpacing(10)

        self._recent_empty_label = QLabel("최근에 연 이미지가 없습니다.")
        self._recent_empty_label.setStyleSheet("color: #6f7278;")

        recent_container = QWidget()
        recent_container.setLayout(self._recent_row)

        recent_scroll = QScrollArea()
        recent_scroll.setWidgetResizable(True)
        recent_scroll.setFixedHeight(150)
        recent_scroll.setFrameShape(QFrame.NoFrame)
        recent_scroll.setWidget(recent_container)

        center = QVBoxLayout()
        center.setAlignment(Qt.AlignTop)
        center.addSpacing(40)
        center.addWidget(title, alignment=Qt.AlignHCenter)
        center.addWidget(subtitle, alignment=Qt.AlignHCenter)
        center.addSpacing(24)
        center.addLayout(cards_layout)
        center.addSpacing(24)
        center.addWidget(QLabel("<b>최근 작업</b>"))
        center.addWidget(self._recent_empty_label)
        center.addWidget(recent_scroll)

        wrapper = QWidget()
        wrapper.setMaximumWidth(720)
        wrapper.setLayout(center)

        outer = QHBoxLayout(self)
        outer.addStretch(1)
        outer.addWidget(wrapper)
        outer.addStretch(1)

        self.set_recent_files([])

    def _on_card_clicked(self, action: str) -> None:
        if action == "open":
            self.open_requested.emit()
        else:
            self.quick_action_requested.emit(action)

    def set_recent_files(self, paths: list[str]) -> None:
        while self._recent_row.count():
            item = self._recent_row.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        existing = [p for p in paths if Path(p).exists()]
        self._recent_empty_label.setVisible(not existing)

        for path in existing:
            card = _RecentFileCard(path)
            card.clicked.connect(lambda _checked=False, p=path: self.recent_file_opened.emit(p))
            self._recent_row.addWidget(card)
        self._recent_row.addStretch(1)
