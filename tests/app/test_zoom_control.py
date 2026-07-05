from app.zoom_control import ZoomControl


def test_zoom_in_and_out_buttons_step_by_ten_percent(qtbot):
    control = ZoomControl()
    qtbot.addWidget(control)

    with qtbot.waitSignal(control.zoom_percent_changed, timeout=1000) as blocker:
        control._on_zoom_in()
    assert blocker.args == [110.0]

    with qtbot.waitSignal(control.zoom_percent_changed, timeout=1000) as blocker:
        control._on_zoom_out()
    assert blocker.args == [100.0]


def test_slider_change_emits_and_updates_label(qtbot):
    control = ZoomControl()
    qtbot.addWidget(control)

    with qtbot.waitSignal(control.zoom_percent_changed, timeout=1000) as blocker:
        control.slider.setValue(175)
    assert blocker.args == [175.0]
    assert control.percent_btn.text() == "175%"


def test_set_zoom_percent_without_emit_only_updates_display(qtbot):
    """캔버스에서 온 동기화 값(예: Ctrl+휠 줌)은 다시 캔버스로 되돌아가는 신호를
    보내면 안 된다 (피드백 루프 방지)."""
    control = ZoomControl()
    qtbot.addWidget(control)

    received = []
    control.zoom_percent_changed.connect(received.append)

    control.set_zoom_percent(180.0)

    assert received == []
    assert control.percent_btn.text() == "180%"
    assert control.slider.value() == 180


def test_fit_button_emits_fit_requested(qtbot):
    control = ZoomControl()
    qtbot.addWidget(control)

    with qtbot.waitSignal(control.fit_requested, timeout=1000):
        control._on_fit_clicked()


def test_zoom_percent_clamped_to_valid_range(qtbot):
    control = ZoomControl()
    qtbot.addWidget(control)

    control.set_zoom_percent(9999)
    assert control.percent_btn.text() == "400%"

    control.set_zoom_percent(-100)
    assert control.percent_btn.text() == "10%"
