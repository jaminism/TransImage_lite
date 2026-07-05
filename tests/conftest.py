import numpy as np
import pytest
from PIL import Image
from PySide6.QtCore import QSettings


@pytest.fixture(autouse=True)
def _isolate_qsettings(tmp_path):
    """MainWindow가 쓰는 QSettings(IniFormat, UserScope, "TransPro", "TransPro")가 실제
    사용자 설정(최근 파일 목록 등)을 건드리지 않도록, 테스트마다 임시 폴더의 ini 파일로
    리다이렉트한다. (주의: QSettings.setDefaultFormat()은 org+app만 받는 2-인자 생성자에
    영향을 주지 않아 효과가 없었다 — MainWindow가 IniFormat을 명시하고, 여기서는
    setPath()로 그 위치만 격리한다.)"""
    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path))
    yield


@pytest.fixture
def sample_rgb_image() -> Image.Image:
    array = np.zeros((20, 30, 3), dtype=np.uint8)
    array[:, :15] = (200, 50, 50)
    array[:, 15:] = (50, 50, 200)
    return Image.fromarray(array, mode="RGB")


@pytest.fixture
def sample_rgba_image(sample_rgb_image: Image.Image) -> Image.Image:
    return sample_rgb_image.convert("RGBA")
