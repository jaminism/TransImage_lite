from app.main_window import PANEL_TEXT, MainWindow


def test_text_reset_clears_fields_and_overlay(qtbot, sample_rgb_image):
    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(sample_rgb_image)
    window._activate_tool_panel(PANEL_TEXT)

    panel = window.text_panel
    panel.text_input.setText("Hello")
    panel.size_spin.setValue(120)
    panel.rotation_spin.setValue(45)
    assert window.canvas._text_item is not None

    panel._on_reset()  # "초기화" 버튼 클릭과 동일한 경로 (reset_requested도 함께 emit됨)

    assert panel.text_input.text() == ""
    assert panel.size_spin.value() == 48
    assert panel.rotation_spin.value() == 0
    assert window.canvas._text_item is None
