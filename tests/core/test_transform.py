from core.processors.transform import ROTATE_LEFT, ROTATE_RIGHT, flip_image, rotate_image


def test_rotate_90_swaps_dimensions(sample_rgb_image):
    result = rotate_image(sample_rgb_image, ROTATE_RIGHT, expand=True)
    w, h = sample_rgb_image.size
    assert result.size == (h, w)


def test_rotate_left_and_right_are_opposite(sample_rgb_image):
    right = rotate_image(sample_rgb_image, ROTATE_RIGHT)
    back = rotate_image(right, ROTATE_LEFT)
    assert back.size == sample_rgb_image.size


def test_rotate_180_keeps_size(sample_rgb_image):
    result = rotate_image(sample_rgb_image, 180)
    assert result.size == sample_rgb_image.size


def test_flip_horizontal_keeps_size(sample_rgb_image):
    result = flip_image(sample_rgb_image, horizontal=True)
    assert result.size == sample_rgb_image.size
    assert result.getpixel((0, 0)) == sample_rgb_image.getpixel((sample_rgb_image.width - 1, 0))


def test_flip_vertical_keeps_size(sample_rgb_image):
    result = flip_image(sample_rgb_image, horizontal=False)
    assert result.size == sample_rgb_image.size
    assert result.getpixel((0, 0)) == sample_rgb_image.getpixel((0, sample_rgb_image.height - 1))
