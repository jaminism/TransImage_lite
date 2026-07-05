from app.main_window import MainWindow


def test_opening_new_image_resets_zoom_to_fit_mode(qtbot, tmp_path, sample_rgb_image):
    """이전 사진에서 수동으로 확대/축소했더라도, 새 사진을 열면 다시 화면에 맞추기부터
    시작해야 한다."""
    path = tmp_path / "sample.png"
    sample_rgb_image.save(path)

    window = MainWindow()
    qtbot.addWidget(window)
    window.resize(900, 700)
    window.show()
    qtbot.wait(10)

    window._open_path(str(path))
    window.canvas.set_zoom_percent(300)
    assert window.canvas._zoom_mode == "manual"

    window._open_path(str(path))
    assert window.canvas._zoom_mode == "fit"


def test_zoom_control_and_canvas_stay_in_sync(qtbot, tmp_path, sample_rgb_image):
    path = tmp_path / "sample.png"
    sample_rgb_image.save(path)

    window = MainWindow()
    qtbot.addWidget(window)
    window._open_path(str(path))

    window.zoom_control.set_zoom_percent(200, emit=True)
    assert window.canvas.current_zoom_percent() == 200.0

    window.canvas.set_zoom_percent(50)
    assert window.zoom_control.percent_btn.text() == "50%"
