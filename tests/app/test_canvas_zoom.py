from PIL import Image

from app.canvas_widget import CanvasWidget


def _make_canvas(qtbot, size=(200, 100)):
    canvas = CanvasWidget()
    qtbot.addWidget(canvas)
    canvas.resize(400, 300)
    canvas.show()
    qtbot.wait(10)
    canvas.set_image(Image.new("RGB", size, (100, 150, 200)))
    return canvas


def test_set_zoom_percent_sets_exact_scale_and_switches_to_manual(qtbot):
    canvas = _make_canvas(qtbot)

    canvas.set_zoom_percent(150)

    assert canvas.current_zoom_percent() == 150.0
    assert canvas._zoom_mode == "manual"


def test_set_zoom_percent_clamps_to_valid_range(qtbot):
    canvas = _make_canvas(qtbot)

    canvas.set_zoom_percent(9999)
    assert canvas.current_zoom_percent() == 400.0

    canvas.set_zoom_percent(-50)
    assert canvas.current_zoom_percent() == 10.0


def test_zoom_changed_signal_emits_on_manual_zoom(qtbot):
    canvas = _make_canvas(qtbot)

    with qtbot.waitSignal(canvas.zoom_changed, timeout=1000) as blocker:
        canvas.set_zoom_percent(200)
    assert blocker.args == [200.0]


def test_zoom_to_fit_switches_mode_back_to_fit(qtbot):
    canvas = _make_canvas(qtbot)
    canvas.set_zoom_percent(300)
    assert canvas._zoom_mode == "manual"

    canvas.zoom_to_fit()
    assert canvas._zoom_mode == "fit"


def test_resize_does_not_change_manual_zoom_but_does_refit_in_fit_mode(qtbot):
    """수동으로 확대/축소한 뒤에는 창 크기를 조절해도 배율이 유지되어야 하고,
    화면에 맞추기 모드일 때는 예전처럼 계속 새 크기에 맞춰 다시 스케일돼야 한다."""
    canvas = _make_canvas(qtbot)

    canvas.set_zoom_percent(250)
    canvas.resize(200, 150)
    qtbot.wait(10)
    assert canvas.current_zoom_percent() == 250.0  # 수동 줌은 리사이즈에 영향받지 않음

    canvas.zoom_to_fit()
    before = canvas.current_zoom_percent()
    canvas.resize(600, 500)
    qtbot.wait(10)
    after = canvas.current_zoom_percent()
    assert after != before  # fit 모드는 리사이즈마다 다시 맞춰짐


def test_wheel_zoom_switches_mode_to_manual(qtbot):
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtGui import QWheelEvent

    canvas = _make_canvas(qtbot)
    assert canvas._zoom_mode == "fit"

    event = QWheelEvent(
        QPoint(10, 10).toPointF(),
        QPoint(10, 10).toPointF(),
        QPoint(0, 0),
        QPoint(0, 120),
        Qt.NoButton,
        Qt.ControlModifier,
        Qt.NoScrollPhase,
        False,
    )
    canvas.wheelEvent(event)

    assert canvas._zoom_mode == "manual"
