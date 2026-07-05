from app.main_window import MainWindow, PANEL_RESIZE


def test_canvas_refits_image_when_window_is_resized(qtbot, sample_rgb_image):
    """사진을 불러온 뒤 창 크기를 조절하면, 도구를 전환했을 때와 마찬가지로 캔버스가
    새 크기에 맞게 다시 스케일되어야 한다. 예전에는 resizeEvent가 busy overlay 위치만
    갱신하고 fitInView()를 다시 호출하지 않아, 창 크기를 조절해도 사진이 그대로
    남아있는 것처럼 보였다."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.resize(1360, 840)
    window.document.load(sample_rgb_image)
    window.center_stack.setCurrentIndex(1)
    window._activate_tool_panel(PANEL_RESIZE)
    window.show()
    qtbot.wait(10)

    before = window.canvas.transform().m11()

    window.resize(700, 500)
    qtbot.wait(10)

    after = window.canvas.transform().m11()
    assert after != before
