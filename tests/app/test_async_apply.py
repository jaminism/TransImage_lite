import app.main_window as main_window_module
from app.main_window import MainWindow
from core.processors.resize import resize_image


def test_async_apply_updates_document(qtbot, sample_rgb_image):
    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(sample_rgb_image)

    window._on_apply_requested(resize_image, {"width": 10, "height": 10, "keep_ratio": False}, True)
    worker = window._worker
    assert worker is not None

    with qtbot.waitSignal(worker.finished_ok, timeout=5000):
        pass
    qtbot.wait(50)

    assert window.document.current.size == (10, 10)
    assert window.document.can_undo()


def test_async_apply_failure_shows_no_crash(qtbot, sample_rgb_image, monkeypatch):
    monkeypatch.setattr(main_window_module.QMessageBox, "critical", lambda *a, **k: None)

    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(sample_rgb_image)

    def _boom(image, **kwargs):
        raise RuntimeError("boom")

    window._on_apply_requested(_boom, {}, True)
    worker = window._worker

    with qtbot.waitSignal(worker.failed, timeout=5000):
        pass
    qtbot.wait(50)

    assert window.document.current.size == sample_rgb_image.size
