from app.info_panel import ImageInfoPanel, format_file_size
from app.main_window import PANEL_ENHANCE, MainWindow


def test_format_file_size():
    assert format_file_size(0) == "0 B"
    assert format_file_size(512) == "512 B"
    assert format_file_size(2048) == "2.0 KB"
    assert format_file_size(5 * 1024 * 1024) == "5.0 MB"


def test_info_panel_defaults_to_placeholder(qtbot):
    panel = ImageInfoPanel()
    qtbot.addWidget(panel)

    assert panel._filename_value.text() == "-"
    assert panel._resolution_value.text() == "-"
    assert panel._size_value.text() == "-"
    assert panel._created_value.text() == "-"


def test_info_panel_shows_filename_and_resolution(qtbot, tmp_path, sample_rgb_image):
    path = tmp_path / "sample.png"
    sample_rgb_image.save(path)

    panel = ImageInfoPanel()
    qtbot.addWidget(panel)
    panel.set_info(str(path), sample_rgb_image)

    assert panel._filename_value.text() == "sample.png"
    assert panel._resolution_value.text() == "30 x 20"
    assert panel._size_value.text() != "-"
    assert panel._created_value.text() != "-"


def test_info_panel_resets_to_placeholder_when_cleared(qtbot, tmp_path, sample_rgb_image):
    path = tmp_path / "sample.png"
    sample_rgb_image.save(path)

    panel = ImageInfoPanel()
    qtbot.addWidget(panel)
    panel.set_info(str(path), sample_rgb_image)
    panel.set_info(None, None)

    assert panel._filename_value.text() == "-"
    assert panel._resolution_value.text() == "-"


def test_opening_image_populates_info_panel(qtbot, tmp_path, sample_rgb_image):
    path = tmp_path / "sample.png"
    sample_rgb_image.save(path)

    window = MainWindow()
    qtbot.addWidget(window)
    window._open_path(str(path))

    assert window.info_panel._filename_value.text() == "sample.png"
    assert window.info_panel._resolution_value.text() == "30 x 20"


def test_closing_image_resets_info_panel(qtbot, tmp_path, sample_rgb_image):
    path = tmp_path / "sample.png"
    sample_rgb_image.save(path)

    window = MainWindow()
    qtbot.addWidget(window)
    window._open_path(str(path))
    window._on_close_image()

    assert window.info_panel._filename_value.text() == "-"


def test_info_panel_stays_visible_when_switching_tools(qtbot, tmp_path, sample_rgb_image):
    """정보 박스는 properties_panel(QStackedWidget)과 달리 어떤 도구를 선택해도 항상
    보여야 한다 — 도구 전환 시 사라지지 않는지 확인하는 회귀 테스트."""
    path = tmp_path / "sample.png"
    sample_rgb_image.save(path)

    window = MainWindow()
    qtbot.addWidget(window)
    window._open_path(str(path))

    window._activate_tool_panel(PANEL_ENHANCE)

    assert not window.info_panel.isHidden()
    assert window.info_panel._filename_value.text() == "sample.png"
