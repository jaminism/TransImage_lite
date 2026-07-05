import pytest

from core.processors.text_overlay import _contains_hangul, add_text, render_text_preview


def test_add_text_returns_rgba(sample_rgb_image):
    result = add_text(sample_rgb_image, "Hi", position=(0, 0), size=10)
    assert result.mode == "RGBA"
    assert result.size == sample_rgb_image.size


def test_add_text_empty_raises(sample_rgb_image):
    with pytest.raises(ValueError):
        add_text(sample_rgb_image, "", size=10)


def test_add_text_rotation(sample_rgb_image):
    result = add_text(sample_rgb_image, "Hi", size=10, rotation=45)
    assert result.mode == "RGBA"


def test_contains_hangul_detects_korean_text():
    assert _contains_hangul("안녕하세요") is True
    assert _contains_hangul("Hello") is False
    assert _contains_hangul("Hello 안녕") is True


def test_render_text_preview_matches_add_text_layer_pixels():
    """미리보기(render_text_preview)와 최종 합성(add_text)이 완전히 같은 레이어를 그려야
    한다 — 그래야 드래그 중 보이는 자간/모양과 실제 적용 결과가 일치한다."""
    from PIL import Image

    preview = render_text_preview("Hello", size=24, color=(255, 255, 255, 255), shadow=True)

    # 텍스트 레이어보다 넉넉히 큰 배경(크롭 시 잘리지 않도록)
    base = Image.new("RGBA", (preview.width + 40, preview.height + 40), (10, 20, 30, 255))
    baked = add_text(base, "Hello", position=(0, 0), size=24, color=(255, 255, 255, 255), shadow=True)

    cropped = baked.crop((0, 0, preview.width, preview.height))
    # 베이스 이미지 위에 합성된 결과이므로, 미리보기 레이어를 같은 베이스에 직접 합성한
    # 결과와 픽셀이 일치해야 완전히 동일한 렌더링 경로임이 증명된다.
    expected = base.crop((0, 0, preview.width, preview.height))
    expected.paste(preview, (0, 0), preview)
    assert cropped.tobytes() == expected.tobytes()


def test_render_text_preview_renders_korean_without_tofu(sample_rgb_image):
    # 한글이 지원되지 않는 폰트를 명시적으로 지정해도(font_path 강제 X), 한글 감지 시
    # 한글 지원 폰트로 대체되어 완전히 빈 레이어가 나오면 안 된다.
    preview = render_text_preview("안녕", size=32, color=(255, 255, 255, 255))
    alpha = preview.split()[-1]
    assert alpha.getextrema()[1] > 0  # 뭔가는 그려졌어야 한다 (전부 투명 == 렌더링 실패)
