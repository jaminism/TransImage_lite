from app.main_window import PANEL_QUALITY, MainWindow
from core.processors.quality import denoise


def test_quality_actions_apply_from_tool_entry_baseline_not_cumulative(qtbot, sample_rgb_image):
    """품질개선 패널에서 값을 바꿔 다시 적용해도 항상 도구 진입 시점 이미지에서부터
    다시 계산해야 한다 — 그렇지 않으면 두 번째 클릭부터는 이미 처리된 결과 위에 또
    처리하는 꼴이라 값을 바꿔도 차이가 거의 안 보여 "고정된" 것처럼 보인다."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(sample_rgb_image)
    window._activate_tool_panel(PANEL_QUALITY)
    baseline = window.document.current

    window._on_apply_requested(denoise, {"strength": 5}, True)
    worker1 = window._worker
    assert worker1._kwargs["image"] is baseline
    with qtbot.waitSignal(worker1.finished_ok, timeout=5000):
        pass
    qtbot.wait(50)
    after_first = window.document.current
    assert after_first is not baseline

    # 두 번째 호출도 (직전 결과가 아니라) 여전히 같은 baseline에서 시작해야 한다.
    window._on_apply_requested(denoise, {"strength": 20}, True)
    worker2 = window._worker
    assert worker2._kwargs["image"] is baseline
    with qtbot.waitSignal(worker2.finished_ok, timeout=5000):
        pass


def test_quality_baseline_updates_when_reentering_tool(qtbot, sample_rgb_image):
    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(sample_rgb_image)

    from app.main_window import PANEL_RESIZE

    window._activate_tool_panel(PANEL_QUALITY)
    first_baseline = window._quality_baseline

    window._activate_tool_panel(PANEL_RESIZE)
    window._on_apply_requested(denoise, {"strength": 5}, True)  # 리사이즈 탭에서는 baseline 미적용(현재 이미지 사용)
    worker = window._worker
    with qtbot.waitSignal(worker.finished_ok, timeout=5000):
        pass
    qtbot.wait(50)

    window._activate_tool_panel(PANEL_QUALITY)
    assert window._quality_baseline is not first_baseline
    assert window._quality_baseline is window.document.current
