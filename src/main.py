import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow

THEME_PATH = Path(__file__).parent / "resources" / "themes" / "dark.qss"


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("TransImage Lite")

    if THEME_PATH.exists():
        app.setStyleSheet(THEME_PATH.read_text(encoding="utf-8"))

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
