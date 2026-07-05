from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton

from app.main_window import PANEL_TEXT, MainWindow


def test_real_button_click_applies_text(qtbot, sample_rgb_image):
    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(sample_rgb_image)
    window._activate_tool_panel(PANEL_TEXT)

    panel = window.text_panel
    qtbot.keyClicks(panel.text_input, "Hello")
    assert panel.text_input.text() == "Hello"
    assert window.canvas._text_item is not None

    before = window.document.current
    buttons = panel.findChildren(QPushButton)
    print("buttons:", [b.text() for b in buttons])
    apply_btn = buttons[-1]
    qtbot.mouseClick(apply_btn, Qt.LeftButton)

    assert window.document.current is not before
