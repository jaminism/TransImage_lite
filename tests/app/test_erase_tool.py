from PySide6.QtCore import QPoint
from PIL import Image

from app.main_window import PANEL_ERASE, PANEL_RESIZE, MainWindow


def test_activating_erase_tool_begins_erase_mode(qtbot, sample_rgb_image):
    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(sample_rgb_image)

    window._activate_tool_panel(PANEL_ERASE)

    assert window.canvas._erase_mode is True
    assert window.canvas._erase_source is not None
    assert window.canvas._erase_preview is not None


def test_leaving_erase_tool_ends_erase_mode(qtbot, sample_rgb_image):
    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(sample_rgb_image)

    window._activate_tool_panel(PANEL_ERASE)
    window._activate_tool_panel(PANEL_RESIZE)

    assert window.canvas._erase_mode is False
    assert window.canvas._erase_source is None
    assert window.canvas._erase_preview is None


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


def test_large_image_uses_downscaled_preview_and_full_res_commit(qtbot):
    """대형 이미지는 축소 프록시로 실시간 표시하고, 스트로크 종료 시에만 원본 해상도로 반영한다."""
    large = Image.new("RGB", (4000, 3000), (200, 100, 50))

    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(large)
    window._activate_tool_panel(PANEL_ERASE)

    canvas = window.canvas
    assert canvas._erase_scale < 1.0
    assert max(canvas._erase_preview.size) <= canvas._PREVIEW_MAX_DIM
    assert canvas._erase_source.size == (4000, 3000)

    # 프록시 좌표계 기준으로 한 번 지운다 (실시간 프리뷰만 갱신됨, 아직 원본은 그대로).
    canvas._erase_at(QPoint(10, 10))
    assert canvas._erase_source.size == (4000, 3000)
    assert len(canvas._stroke_points) == 1

    canvas._commit_erase_stroke()

    # 커밋 후에는 원본 해상도 그대로 유지되어야 한다 (축소된 채로 저장되면 안 됨).
    assert canvas._erase_source.size == (4000, 3000)
    assert canvas._stroke_points == []


def test_erase_at_without_active_erase_is_noop(qtbot, sample_rgb_image):
    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(sample_rgb_image)
    # 지우개 모드가 아닌 상태에서 호출해도 예외가 나면 안 된다.
    window.canvas._erase_at(QPoint(1, 1))
