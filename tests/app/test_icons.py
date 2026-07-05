from app.icons import icon


def test_icon_rasterizes_non_null(qtbot):
    ic = icon("save")
    assert not ic.isNull()
    pixmap = ic.pixmap(24, 24)
    assert not pixmap.isNull()
    assert pixmap.width() > 0 and pixmap.height() > 0


def test_icon_is_cached(qtbot):
    assert icon("undo") is icon("undo")


def test_zoom_icons_rasterize_non_null(qtbot):
    for name in ("zoom_in", "zoom_out", "zoom_fit"):
        ic = icon(name)
        assert not ic.isNull()
        pixmap = ic.pixmap(24, 24)
        assert not pixmap.isNull()
