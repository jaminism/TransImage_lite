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
