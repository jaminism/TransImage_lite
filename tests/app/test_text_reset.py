from app.main_window import PANEL_TEXT, MainWindow


def test_text_shadow_defaults_to_unchecked(qtbot, sample_rgb_image):
    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(sample_rgb_image)
    window._activate_tool_panel(PANEL_TEXT)

    assert window.text_panel.shadow_check.isChecked() is False
    assert window.text_panel.current_params()["shadow"] is False


def test_text_reset_clears_fields_and_overlay(qtbot, sample_rgb_image):
    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(sample_rgb_image)
    window._activate_tool_panel(PANEL_TEXT)

    panel = window.text_panel
    panel.text_input.setText("Hello")
    panel.size_spin.setValue(20)
    panel.rotation_spin.setValue(45)
    panel.shadow_check.setChecked(True)
    assert window.canvas._text_handle is not None

    panel._on_reset()  # "초기화" 버튼 클릭과 동일한 경로 (reset_requested도 함께 emit됨)

    assert panel.text_input.text() == ""
    assert panel.size_spin.value() == 6
    assert panel.rotation_spin.value() == 0
    assert panel.shadow_check.isChecked() is False
    assert window.canvas._text_handle is None


def test_text_reset_reverts_already_applied_text(qtbot, sample_rgb_image):
    """텍스트를 "적용"(baked)한 뒤 "초기화"를 누르면, 이 도구에 들어왔을 때 상태로
    실제 이미지도 되돌아가야 한다 — 입력 필드만 비우는 건 사용자 입장에서
    "초기화가 안 된다"로 보인다."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(sample_rgb_image)
    window._activate_tool_panel(PANEL_TEXT)
    baseline = window.document.current

    window.text_panel.text_input.setText("Hello")
    window._on_text_apply(
        {"text": "Hello", "size_percent": 6, "color": (255, 255, 255, 255), "rotation": 0.0, "shadow": True}
    )
    assert window.document.current is not baseline

    window.text_panel._on_reset()

    assert window.document.current is baseline
    assert window.document.can_undo()
