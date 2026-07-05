from app.panels.resize_panel import ResizePanel


def test_angle_apply_emits_dedicated_signal_with_spin_value(qtbot):
    panel = ResizePanel()
    qtbot.addWidget(panel)

    panel.angle_spin.setValue(37)

    with qtbot.waitSignal(panel.angle_apply_requested, timeout=1000) as blocker:
        panel._on_apply_angle()

    assert blocker.args == [37.0]


def test_angle_apply_supports_negative_angle(qtbot):
    panel = ResizePanel()
    qtbot.addWidget(panel)

    panel.angle_spin.setValue(-90)

    with qtbot.waitSignal(panel.angle_apply_requested, timeout=1000) as blocker:
        panel._on_apply_angle()

    assert blocker.args == [-90.0]
