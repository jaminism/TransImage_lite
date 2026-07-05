from PIL import Image
from PySide6.QtCore import QPointF

from app.main_window import PANEL_BACKGROUND, PANEL_RESIZE, MainWindow


def test_lasso_toggle_starts_and_stops_lasso_mode(qtbot, sample_rgba_image):
    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(sample_rgba_image)
    window._activate_tool_panel(PANEL_BACKGROUND)

    window.background_panel.lasso_btn.setChecked(True)
    assert window.canvas._lasso_mode is True
    assert window.canvas._erase_source is not None

    window.background_panel.lasso_btn.setChecked(False)
    assert window.canvas._lasso_mode is False
    assert window.canvas._erase_source is None


def test_switching_tool_away_ends_lasso_mode(qtbot, sample_rgba_image):
    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(sample_rgba_image)
    window._activate_tool_panel(PANEL_BACKGROUND)
    window.background_panel.lasso_btn.setChecked(True)

    window._activate_tool_panel(PANEL_RESIZE)

    assert window.canvas._lasso_mode is False
    assert window.background_panel.lasso_btn.isChecked() is False


def test_lasso_selection_erases_only_enclosed_region(qtbot):
    img = Image.new("RGB", (100, 100), (10, 20, 30))
    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(img)
    window._activate_tool_panel(PANEL_BACKGROUND)
    window.background_panel.lasso_btn.setChecked(True)

    canvas = window.canvas
    # 100x100은 축소 프록시 없이(scale=1.0) 표시되므로 프록시 좌표 == 원본 좌표.
    canvas._lasso_points = [QPointF(x, y) for x, y in [(10, 10), (30, 10), (30, 30), (10, 30)]]
    canvas._commit_lasso_selection()

    result = window.document.current
    assert result.mode == "RGBA"
    # 올가미 내부(20,20)는 투명, 바깥(80,80)은 그대로 불투명해야 한다.
    assert result.getpixel((20, 20))[3] == 0
    assert result.getpixel((80, 80))[3] == 255


def test_lasso_without_image_shows_message_and_unchecks(qtbot, monkeypatch):
    import app.main_window as main_window_module

    monkeypatch.setattr(main_window_module.QMessageBox, "information", lambda *a, **k: None)

    window = MainWindow()
    qtbot.addWidget(window)
    window._activate_tool_panel(PANEL_BACKGROUND)

    window.background_panel.lasso_btn.setChecked(True)

    assert window.background_panel.lasso_btn.isChecked() is False
    assert window.canvas._lasso_mode is False
