from app.panels.resize_panel import ResizePanel
from core.processors.transform import rotate_image


def test_angle_apply_emits_rotate_with_spin_value(qtbot):
    panel = ResizePanel()
    qtbot.addWidget(panel)

    panel.angle_spin.setValue(37)

    with qtbot.waitSignal(panel.apply_requested, timeout=1000) as blocker:
        panel._on_apply_angle()

    fn, kwargs, is_async = blocker.args
    assert fn is rotate_image
    assert kwargs == {"angle": 37.0}
    assert is_async is False


def test_angle_apply_supports_negative_angle(qtbot):
    panel = ResizePanel()
    qtbot.addWidget(panel)

    panel.angle_spin.setValue(-90)

    with qtbot.waitSignal(panel.apply_requested, timeout=1000) as blocker:
        panel._on_apply_angle()

    _fn, kwargs, _is_async = blocker.args
    assert kwargs == {"angle": -90.0}
