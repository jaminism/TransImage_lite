import app.main_window as main_window_module
from app.main_window import PANEL_TEXT, STACK_EDITOR, STACK_HOME, MainWindow


def test_starts_on_home_screen(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    assert window.center_stack.currentIndex() == STACK_HOME


def test_opening_image_switches_to_editor(qtbot, tmp_path, sample_rgb_image):
    path = tmp_path / "sample.png"
    sample_rgb_image.save(path)

    window = MainWindow()
    qtbot.addWidget(window)
    window._open_path(str(path))

    assert window.center_stack.currentIndex() == STACK_EDITOR
    assert window.document.current is not None


def test_close_image_returns_to_home_and_clears_document(qtbot, tmp_path, sample_rgb_image):
    path = tmp_path / "sample.png"
    sample_rgb_image.save(path)

    window = MainWindow()
    qtbot.addWidget(window)
    window._open_path(str(path))

    window._on_close_image()

    assert window.center_stack.currentIndex() == STACK_HOME
    assert window.document.current is None
    assert not window.close_action.isEnabled()


def test_close_image_with_edits_asks_confirmation(qtbot, tmp_path, sample_rgb_image, monkeypatch):
    from core.processors.resize import resize_image

    path = tmp_path / "sample.png"
    sample_rgb_image.save(path)

    window = MainWindow()
    qtbot.addWidget(window)
    window._open_path(str(path))
    window.document.apply(resize_image, width=5, height=5, keep_ratio=False)

    monkeypatch.setattr(main_window_module.QMessageBox, "question", lambda *a, **k: main_window_module.QMessageBox.No)
    window._on_close_image()
    assert window.center_stack.currentIndex() == STACK_EDITOR  # 취소했으니 그대로 유지

    monkeypatch.setattr(
        main_window_module.QMessageBox, "question", lambda *a, **k: main_window_module.QMessageBox.Yes
    )
    window._on_close_image()
    assert window.center_stack.currentIndex() == STACK_HOME


def test_opening_image_remembers_recent_file(qtbot, tmp_path, sample_rgb_image):
    path = tmp_path / "sample.png"
    sample_rgb_image.save(path)

    window = MainWindow()
    qtbot.addWidget(window)
    window._open_path(str(path))

    recent = window._settings.value("recentFiles", [], type=list)
    assert str(path) in recent


def test_recent_file_card_reopens_image(qtbot, tmp_path, sample_rgb_image):
    path = tmp_path / "sample.png"
    sample_rgb_image.save(path)

    window = MainWindow()
    qtbot.addWidget(window)
    window._open_path(str(path))
    window._on_close_image()
    assert window.center_stack.currentIndex() == STACK_HOME

    window.home_widget.recent_file_opened.emit(str(path))

    assert window.center_stack.currentIndex() == STACK_EDITOR
    assert window.document.current is not None


def test_home_quick_action_opens_file_and_selects_tool(qtbot, tmp_path, sample_rgb_image, monkeypatch):
    path = tmp_path / "sample.png"
    sample_rgb_image.save(path)

    window = MainWindow()
    qtbot.addWidget(window)

    monkeypatch.setattr(
        main_window_module.QFileDialog, "getOpenFileName", lambda *a, **k: (str(path), "")
    )

    window._on_home_quick_action("text")

    assert window.center_stack.currentIndex() == STACK_EDITOR
    assert window.properties_panel.currentIndex() == PANEL_TEXT


def test_sidebar_and_properties_panel_stay_visible_on_home_screen(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.center_stack.currentIndex() == STACK_HOME
    assert not window.sidebar.isHidden()
    assert not window.properties_panel.isHidden()

    # 이미지 없이도 사이드바에서 도구를 미리 선택해둘 수 있어야 한다.
    from app.main_window import PANEL_QUALITY

    row = next(r for r, idx in window._tool_rows.items() if idx == PANEL_QUALITY)
    window.sidebar.setCurrentRow(row)
    assert window.properties_panel.currentIndex() == PANEL_QUALITY


def test_home_widget_filters_out_missing_recent_files(qtbot, tmp_path):
    from app.home_widget import HomeWidget

    widget = HomeWidget()
    qtbot.addWidget(widget)

    missing = str(tmp_path / "does-not-exist.png")
    widget.set_recent_files([missing])

    assert not widget._recent_empty_label.isHidden()


def test_home_widget_clear_recent_button_visibility(qtbot, tmp_path, sample_rgb_image):
    from app.home_widget import HomeWidget

    widget = HomeWidget()
    qtbot.addWidget(widget)
    assert widget._clear_recent_button.isHidden()

    path = tmp_path / "sample.png"
    sample_rgb_image.save(path)
    widget.set_recent_files([str(path)])
    assert not widget._clear_recent_button.isHidden()

    widget.set_recent_files([])
    assert widget._clear_recent_button.isHidden()


def test_clear_recent_files_asks_confirmation_and_empties_list(
    qtbot, tmp_path, sample_rgb_image, monkeypatch
):
    path = tmp_path / "sample.png"
    sample_rgb_image.save(path)

    window = MainWindow()
    qtbot.addWidget(window)
    window._open_path(str(path))
    window._on_close_image()

    assert str(path) in window._settings.value("recentFiles", [], type=list)

    monkeypatch.setattr(main_window_module.QMessageBox, "question", lambda *a, **k: main_window_module.QMessageBox.No)
    window.home_widget.clear_recent_requested.emit()
    assert str(path) in window._settings.value("recentFiles", [], type=list)

    monkeypatch.setattr(main_window_module.QMessageBox, "question", lambda *a, **k: main_window_module.QMessageBox.Yes)
    window.home_widget.clear_recent_requested.emit()
    assert window._settings.value("recentFiles", [], type=list) == []
    assert window.home_widget._clear_recent_button.isHidden()
