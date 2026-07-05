import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow

RESOURCES_DIR = Path(__file__).parent / "resources"
THEME_PATH = RESOURCES_DIR / "themes" / "dark.qss"
APP_ICON_PATH = RESOURCES_DIR / "icons" / "app.ico"


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Trans Pro")

    if THEME_PATH.exists():
        app.setStyleSheet(THEME_PATH.read_text(encoding="utf-8"))
    if APP_ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(APP_ICON_PATH)))

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
