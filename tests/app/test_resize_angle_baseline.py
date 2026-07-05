from app.main_window import PANEL_RESIZE, MainWindow


def test_applying_zero_after_nonzero_angle_reverts_to_baseline(qtbot, sample_rgb_image):
    """5도를 적용한 뒤 0도로 다시 적용하면 정확히 원래 상태(baseline)로 돌아와야 한다.
    document.current(직전 결과)에 매번 상대 회전을 누적 적용하면, 이미 5도 회전된
    이미지에 0도(무변화)가 적용될 뿐이라 원래대로 돌아오지 않는 버그가 있었다."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(sample_rgb_image)
    window._activate_tool_panel(PANEL_RESIZE)
    baseline = window.document.current

    window._on_angle_apply(5.0)
    assert window.document.current.tobytes() != baseline.tobytes()

    window._on_angle_apply(0.0)
    assert window.document.current.tobytes() == baseline.tobytes()
    assert window.document.current.size == baseline.size


def test_repeated_angle_applies_are_absolute_not_cumulative(qtbot, sample_rgb_image):
    """10도 적용 후 20도를 적용하면 baseline 기준 20도 회전 결과여야 한다(10+20=30이 아님)."""
    from core.processors.transform import rotate_image

    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(sample_rgb_image)
    window._activate_tool_panel(PANEL_RESIZE)
    baseline = window.document.current

    window._on_angle_apply(10.0)
    window._on_angle_apply(20.0)

    expected = rotate_image(baseline, 20.0)
    assert window.document.current.tobytes() == expected.tobytes()


def test_angle_apply_builds_on_committed_icon_rotation(qtbot, sample_rgb_image):
    """아이콘 회전(90도) 같은 일반 apply_requested 액션이 커밋되면, 각도 직접 입력의
    baseline도 그 결과로 갱신되어야 한다 — 그래야 각도 입력이 아이콘 회전을 지우지 않는다."""
    from core.processors.resize import resize_image

    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(sample_rgb_image)
    window._activate_tool_panel(PANEL_RESIZE)

    window._on_apply_requested(resize_image, {"width": 50, "height": 50, "keep_ratio": False}, False)
    after_resize = window.document.current
    assert window._resize_baseline is after_resize

    window._on_angle_apply(0.0)
    assert window.document.current.tobytes() == after_resize.tobytes()
    assert window.document.current.size == after_resize.size
