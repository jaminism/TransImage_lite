import pytest

from core.image_document import ImageDocument
from core.processors.resize import resize_image


def test_load_sets_current_and_original(sample_rgb_image):
    doc = ImageDocument()
    doc.load(sample_rgb_image)
    assert doc.current is not None
    assert doc.original is not None


def test_apply_and_undo_redo(sample_rgb_image):
    doc = ImageDocument()
    doc.load(sample_rgb_image)
    doc.apply(resize_image, width=10, height=10, keep_ratio=False)
    assert doc.current.size == (10, 10)
    assert doc.can_undo()

    doc.undo()
    assert doc.current.size == sample_rgb_image.size
    assert doc.can_redo()

    doc.redo()
    assert doc.current.size == (10, 10)


def test_apply_without_image_raises():
    doc = ImageDocument()
    with pytest.raises(ValueError):
        doc.apply(resize_image, width=10)


def test_apply_result(sample_rgb_image):
    doc = ImageDocument()
    doc.load(sample_rgb_image)
    new_image = resize_image(sample_rgb_image, width=5, height=5, keep_ratio=False)
    doc.apply_result(new_image)
    assert doc.current.size == (5, 5)
    assert doc.can_undo()
