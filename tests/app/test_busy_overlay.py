from app.main_window import MainWindow
from core.processors.quality import denoise


def test_busy_overlay_shows_during_async_and_hides_after(qtbot, sample_rgb_image):
    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(sample_rgb_image)

    window._on_apply_requested(denoise, {"strength": 5}, True)
    assert not window.canvas._busy_overlay.isHidden()
    assert "노이즈 제거" in window.statusBar().currentMessage()

    worker = window._worker
    with qtbot.waitSignal(worker.finished_ok, timeout=5000):
        pass
    qtbot.wait(50)

    assert window.canvas._busy_overlay.isHidden()


def test_busy_overlay_animation_timer_runs_only_while_visible(qtbot, sample_rgb_image):
    """단조로운 진행률 막대 대신 스캔 라인/스파클 애니메이션을 그리는데, 숨겨진
    동안에도 타이머가 계속 돌면 불필요하게 CPU를 쓰므로 보이는 동안에만 동작해야 한다."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(sample_rgb_image)

    overlay = window.canvas._busy_overlay
    assert not overlay._timer.isActive()

    window.canvas.set_busy(True, "처리 중...")
    assert overlay._timer.isActive()

    window.canvas.set_busy(False)
    assert not overlay._timer.isActive()


def test_busy_overlay_animation_advances_scan_position_and_spawns_sparkles(qtbot, sample_rgb_image):
    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(sample_rgb_image)

    overlay = window.canvas._busy_overlay
    window.canvas.set_busy(True, "처리 중...")

    initial_scan_y = overlay._scan_y
    for _ in range(200):
        overlay._on_tick()

    assert overlay._scan_y != initial_scan_y
    assert len(overlay._sparkles) > 0
