import pytest

from core.processors.io import open_image, save_image


def test_save_and_open_png(tmp_path, sample_rgba_image):
    path = tmp_path / "out.png"
    save_image(sample_rgba_image, str(path))
    loaded = open_image(str(path))
    assert loaded.size == sample_rgba_image.size


def test_save_jpeg_flattens_alpha(tmp_path, sample_rgba_image):
    path = tmp_path / "out.jpg"
    save_image(sample_rgba_image, str(path))
    loaded = open_image(str(path))
    assert loaded.mode == "RGB"


def test_open_unsupported_extension_raises(tmp_path):
    path = tmp_path / "out.gif"
    path.write_bytes(b"GIF89a")
    with pytest.raises(ValueError):
        open_image(str(path))


def test_save_unsupported_extension_raises(tmp_path, sample_rgb_image):
    path = tmp_path / "out.tiff"
    with pytest.raises(ValueError):
        save_image(sample_rgb_image, str(path))
