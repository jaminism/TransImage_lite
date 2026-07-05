from PySide6.QtCore import QPointF

from app.main_window import PANEL_TEXT, MainWindow

_PADDING = 8  # canvas_widget._TEXT_PADDING과 동일해야 함


def test_text_overlay_appears_and_is_draggable(qtbot, sample_rgb_image):
    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(sample_rgb_image)
    window._activate_tool_panel(PANEL_TEXT)

    window.text_panel.text_input.setText("Hello")
    assert window.canvas._text_handle is not None
    assert window.canvas._text_item is not None

    window.canvas._text_handle.setPos(QPointF(7, 9))
    assert window.canvas.get_text_overlay_position() == (7 + _PADDING, 9 + _PADDING)


def test_text_apply_bakes_text_at_dragged_position(qtbot, sample_rgb_image):
    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(sample_rgb_image)
    window._activate_tool_panel(PANEL_TEXT)

    window.text_panel.text_input.setText("Hi")
    window.canvas._text_handle.setPos(QPointF(3, 4))

    before = window.document.current
    window._on_text_apply(
        {"text": "Hi", "size_percent": 6, "color": (255, 255, 255, 255), "rotation": 0.0, "shadow": True}
    )

    assert window.document.current is not before
    assert window.document.current.mode == "RGBA"
    assert window.canvas._text_handle is None  # applied -> overlay cleared
    assert window.canvas._text_item is None


def test_text_apply_without_text_shows_message_and_does_not_change_document(qtbot, sample_rgb_image, monkeypatch):
    import app.main_window as main_window_module

    monkeypatch.setattr(main_window_module.QMessageBox, "information", lambda *a, **k: None)

    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(sample_rgb_image)
    window._activate_tool_panel(PANEL_TEXT)

    before = window.document.current
    window._on_text_apply({"text": "   ", "size_percent": 6, "color": (255, 255, 255, 255), "rotation": 0.0})

    assert window.document.current is before


def test_text_size_percent_scales_with_image_height(qtbot):
    from PIL import Image

    window = MainWindow()
    qtbot.addWidget(window)

    window.document.load(Image.new("RGB", (200, 100), (0, 0, 0)))
    assert window._resolve_text_pixel_size(10) == 10  # 100 * 10% = 10

    window.document.load(Image.new("RGB", (200, 1000), (0, 0, 0)))
    assert window._resolve_text_pixel_size(10) == 100  # 1000 * 10% = 100
