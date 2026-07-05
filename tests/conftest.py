import numpy as np
import pytest
from PIL import Image


@pytest.fixture
def sample_rgb_image() -> Image.Image:
    array = np.zeros((20, 30, 3), dtype=np.uint8)
    array[:, :15] = (200, 50, 50)
    array[:, 15:] = (50, 50, 200)
    return Image.fromarray(array, mode="RGB")


@pytest.fixture
def sample_rgba_image(sample_rgb_image: Image.Image) -> Image.Image:
    return sample_rgb_image.convert("RGBA")
