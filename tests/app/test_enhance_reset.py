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
