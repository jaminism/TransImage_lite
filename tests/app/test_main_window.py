import app.main_window as main_window_module
from app.main_window import PANEL_QUALITY, TOOL_PANEL_LABELS, MainWindow


def _tool_row(window, label: str) -> int:
    for row, kind in window._row_kind.items():
        if kind == "tool" and window.sidebar.item(row).text() == label:
            return row
    raise AssertionError(f"tool row not found for label: {label}")


def test_main_window_launches(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    assert window.windowTitle() == "Trans Pro"
    assert window.properties_panel.count() == len(TOOL_PANEL_LABELS)


def test_tool_switch_updates_panel(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    row = _tool_row(window, "품질 개선")
    window.sidebar.setCurrentRow(row)
    assert window.properties_panel.currentIndex() == PANEL_QUALITY


def test_action_row_does_not_change_panel_and_restores_selection(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    resize_row = _tool_row(window, "크기 / 회전")
    window.sidebar.setCurrentRow(resize_row)

    called = []
    print_row = next(r for r, kind in window._row_kind.items() if kind == "action")
    window._action_handlers[print_row] = lambda: called.append(True)
    window.sidebar.setCurrentRow(print_row)

    assert called == [True]
    assert window.sidebar.currentRow() == resize_row
    assert window.properties_panel.currentIndex() == 0


def test_open_image_updates_document_and_canvas(qtbot, tmp_path, sample_rgb_image):
    path = tmp_path / "sample.png"
    sample_rgb_image.save(path)

    window = MainWindow()
    qtbot.addWidget(window)

    from core.processors.io import open_image

    window.document.load(open_image(str(path)))
    window._refresh_canvas()
    window._update_actions_enabled()

    assert window.document.current is not None
    assert window.save_action.isEnabled()


def test_quick_save_writes_to_opened_path(qtbot, tmp_path, sample_rgb_image):
    path = tmp_path / "sample.png"
    sample_rgb_image.save(path)

    window = MainWindow()
    qtbot.addWidget(window)

    from core.processors.io import open_image

    window.document.load(open_image(str(path)))
    window._current_path = str(path)

    window._on_quick_save()

    from core.processors.io import open_image as reopen

    reloaded = reopen(str(path))
    assert reloaded.size == sample_rgb_image.size


def test_save_as_updates_current_path(qtbot, tmp_path, sample_rgb_image, monkeypatch):
    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(sample_rgb_image)

    new_path = tmp_path / "renamed.png"
    monkeypatch.setattr(
        main_window_module.QFileDialog,
        "getSaveFileName",
        lambda *a, **k: (str(new_path), "PNG (*.png)"),
    )

    window._on_save_as()

    assert window._current_path == str(new_path)
    assert new_path.exists()


def test_save_dialog_start_path_empty_when_no_current_path(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    assert window._save_dialog_start_path() == ""


def test_save_dialog_start_path_falls_back_when_directory_missing(qtbot, tmp_path):
    window = MainWindow()
    qtbot.addWidget(window)
    missing_dir_path = str(tmp_path / "no-such-folder" / "photo.png")
    window._current_path = missing_dir_path

    result = window._save_dialog_start_path()

    assert result == "photo.png"


def test_save_dialog_start_path_kept_when_directory_exists(qtbot, tmp_path):
    window = MainWindow()
    qtbot.addWidget(window)
    existing_path = str(tmp_path / "photo.png")
    window._current_path = existing_path

    assert window._save_dialog_start_path() == existing_path


def test_quick_save_falls_back_to_save_as_when_original_dir_missing(qtbot, tmp_path, sample_rgb_image, monkeypatch):
    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(sample_rgb_image)
    window._current_path = str(tmp_path / "gone" / "photo.png")

    called = []
    monkeypatch.setattr(window, "_on_save_as", lambda: called.append(True))

    window._on_quick_save()

    assert called == [True]


def test_reset_all_reverts_to_original(qtbot, sample_rgb_image):
    from core.processors.resize import resize_image

    window = MainWindow()
    qtbot.addWidget(window)
    window.document.load(sample_rgb_image)

    window.document.apply(resize_image, width=5, height=5, keep_ratio=False)
    assert window.document.current.size == (5, 5)

    monkey_confirmed = True
    import PySide6.QtWidgets as qtw

    orig_question = qtw.QMessageBox.question
    qtw.QMessageBox.question = staticmethod(lambda *a, **k: qtw.QMessageBox.Yes)
    try:
        window._on_reset_all()
    finally:
        qtw.QMessageBox.question = orig_question

    assert window.document.current.size == sample_rgb_image.size
    assert monkey_confirmed
