from app.main_window import PANEL_ERASE, PANEL_RESIZE, MainWindow


def test_activating_erase_tool_begins_erase_mode(qtbot, sample_rgb_image):
    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(sample_rgb_image)

    window._activate_tool_panel(PANEL_ERASE)

    assert window.canvas._erase_mode is True
    assert window.canvas._erase_image is not None


def test_leaving_erase_tool_ends_erase_mode(qtbot, sample_rgb_image):
    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(sample_rgb_image)

    window._activate_tool_panel(PANEL_ERASE)
    window._activate_tool_panel(PANEL_RESIZE)

    assert window.canvas._erase_mode is False
    assert window.canvas._erase_image is None


def test_erase_stroke_finished_commits_to_document(qtbot, sample_rgba_image):
    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(sample_rgba_image)
    window._activate_tool_panel(PANEL_ERASE)

    erased = sample_rgba_image.copy()
    erased.putpixel((0, 0), (0, 0, 0, 0))

    before = window.document.current
    window.canvas.erase_stroke_finished.emit(erased)

    assert window.document.current is erased
    assert window.document.current is not before
    assert window.document.can_undo()


def test_brush_size_slider_updates_canvas(qtbot, sample_rgb_image):
    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(sample_rgb_image)
    window._activate_tool_panel(PANEL_ERASE)

    window.erase_panel.brush_slider.setValue(50)

    assert window.canvas._brush_radius == 50
