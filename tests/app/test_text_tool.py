from PySide6.QtCore import QPointF

from app.main_window import PANEL_TEXT, MainWindow


def test_text_overlay_appears_and_is_draggable(qtbot, sample_rgb_image):
    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(sample_rgb_image)
    window._activate_tool_panel(PANEL_TEXT)

    window.text_panel.text_input.setText("Hello")
    assert window.canvas._text_item is not None

    window.canvas._text_item.setPos(QPointF(7, 9))
    assert window.canvas.get_text_overlay_position() == (7, 9)


def test_text_apply_bakes_text_at_dragged_position(qtbot, sample_rgb_image):
    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(sample_rgb_image)
    window._activate_tool_panel(PANEL_TEXT)

    window.text_panel.text_input.setText("Hi")
    window.canvas._text_item.setPos(QPointF(3, 4))

    before = window.document.current
    window._on_text_apply(
        {"text": "Hi", "size": 12, "color": (255, 255, 255, 255), "rotation": 0.0, "shadow": True}
    )

    assert window.document.current is not before
    assert window.document.current.mode == "RGBA"
    assert window.canvas._text_item is None  # applied -> overlay cleared


def test_text_apply_without_text_shows_message_and_does_not_change_document(qtbot, sample_rgb_image, monkeypatch):
    import app.main_window as main_window_module

    monkeypatch.setattr(main_window_module.QMessageBox, "information", lambda *a, **k: None)

    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(sample_rgb_image)
    window._activate_tool_panel(PANEL_TEXT)

    before = window.document.current
    window._on_text_apply({"text": "   ", "size": 12, "color": (255, 255, 255, 255), "rotation": 0.0})

    assert window.document.current is before
