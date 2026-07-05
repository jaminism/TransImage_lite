from app.main_window import TOOL_NAMES, MainWindow


def test_main_window_launches(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    assert window.windowTitle() == "TransImage Lite"
    assert window.properties_panel.count() == len(TOOL_NAMES)


def test_tool_switch_updates_panel(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.sidebar.setCurrentRow(2)
    assert window.properties_panel.currentIndex() == 2


def test_open_image_updates_document_and_canvas(qtbot, tmp_path, sample_rgb_image):
    path = tmp_path / "sample.png"
    sample_rgb_image.save(path)

    window = MainWindow()
    qtbot.addWidget(window)

    from core.processors.io import open_image

    window.document.load(open_image(str(path)))
    window._refresh_canvas()
    window._update_actions_enabled()

    assert window.document.current is not None
    assert window.save_action.isEnabled()
