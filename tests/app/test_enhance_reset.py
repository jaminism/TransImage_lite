from app.main_window import PANEL_ENHANCE, MainWindow
from core.processors.enhance import apply_adjustments


def test_reset_reverts_committed_adjustment_to_panel_baseline(qtbot, sample_rgb_image):
    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(sample_rgb_image)

    window._activate_tool_panel(PANEL_ENHANCE)
    baseline = window.document.current

    # 슬라이더 조정 후 "적용"을 누른 것과 동일한 효과 (커밋됨)
    window.document.apply(apply_adjustments, brightness=1.5, contrast=1.2, saturation=0.8)
    assert window.document.current is not baseline

    window.enhance_panel.reset_requested.emit()

    assert window.document.current is baseline
    assert window.document.can_undo()  # 초기화 자체도 undo 가능해야 한다


def test_reset_is_noop_when_nothing_applied(qtbot, sample_rgb_image):
    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(sample_rgb_image)

    window._activate_tool_panel(PANEL_ENHANCE)
    baseline = window.document.current

    window.enhance_panel.reset_requested.emit()

    assert window.document.current is baseline


def test_reset_refreshes_canvas_when_only_live_preview_was_shown(qtbot, sample_rgb_image):
    """슬라이더로 미리보기만 본 상태(적용 안 누름)에서 초기화를 누르면, document.current는
    이미 baseline과 같아도 캔버스에는 커밋되지 않은 미리보기가 남아있으므로 반드시
    다시 그려야 한다."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(sample_rgb_image)

    window._activate_tool_panel(PANEL_ENHANCE)
    baseline = window.document.current

    # 슬라이더 드래그로 인한 라이브 미리보기 — document.current는 그대로, 캔버스만 바뀜
    window._on_preview_requested(apply_adjustments, {"brightness": 1.8, "contrast": 1.5, "saturation": 0.5})
    previewed = window.canvas._pixmap_item.pixmap().toImage()

    window.enhance_panel.reset_requested.emit()

    assert window.document.current is baseline
    reverted = window.canvas._pixmap_item.pixmap().toImage()
    assert reverted != previewed
