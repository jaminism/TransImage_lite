from PIL import Image

from app.canvas_widget import CanvasWidget, _has_transparency


def test_has_transparency_detects_partial_alpha():
    opaque = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
    assert _has_transparency(opaque) is False

    partially_transparent = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
    partially_transparent.putpixel((0, 0), (255, 0, 0, 0))
    assert _has_transparency(partially_transparent) is True


def test_has_transparency_false_for_rgb():
    rgb = Image.new("RGB", (10, 10), (255, 0, 0))
    assert _has_transparency(rgb) is False


def test_canvas_shows_checkerboard_only_for_transparent_images(qtbot):
    """배경 제거로 투명해진 이미지는 캔버스 크기가 그대로인데도 캔버스 배경색과
    비슷해 보여 사진이 작아진 것처럼 보이는 착시가 있었다 — 체커보드로 투명 영역을
    명확히 표시해야 한다. 불투명 이미지에는 체커보드가 필요 없다."""
    canvas = CanvasWidget()
    qtbot.addWidget(canvas)

    opaque = Image.new("RGB", (50, 40), (100, 150, 200))
    canvas.set_image(opaque)
    assert canvas._checkerboard_item is None

    transparent = Image.new("RGBA", (50, 40), (0, 0, 0, 0))
    transparent.paste(Image.new("RGBA", (20, 20), (255, 0, 0, 255)), (10, 10))
    canvas.set_image(transparent)
    assert canvas._checkerboard_item is not None
    rect = canvas._checkerboard_item.rect()
    assert (rect.width(), rect.height()) == (50, 40)


def test_canvas_clears_checkerboard_when_switching_back_to_opaque_image(qtbot):
    canvas = CanvasWidget()
    qtbot.addWidget(canvas)

    transparent = Image.new("RGBA", (30, 30), (0, 0, 0, 0))
    canvas.set_image(transparent)
    assert canvas._checkerboard_item is not None

    opaque = Image.new("RGB", (30, 30), (10, 20, 30))
    canvas.set_image(opaque)
    assert canvas._checkerboard_item is None
