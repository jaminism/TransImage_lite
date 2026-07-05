---
name: image-processing-recipes
description: "Pillow/OpenCV/rembg 기반 이미지 처리 레시피 라이브러리. 리사이즈, 노이즈 제거/선명도(품질 개선), 텍스트 오버레이, 밝기/대비/채도 보정, 배경 제거, 프린트용 스케일링의 구체적인 코드 패턴과 파라미터 가이드를 제공하는 imaging-engineer 확장 스킬. '이미지 리사이즈', '노이즈 제거', '선명도 향상', '업스케일', '텍스트 오버레이', '색보정', '배경 제거', 'rembg' 등 이미지 처리 알고리즘 구현 시 사용한다. 단, UI 위젯 구현이나 앱 패키징은 이 스킬의 범위가 아니다."
---

# Image Processing Recipes — 이미지 처리 레시피

imaging-engineer 에이전트가 각 기능을 구현할 때 참조하는 Pillow/OpenCV/rembg 구체 레시피와 파라미터 가이드.

## 대상 에이전트

`imaging-engineer` — 이 스킬의 레시피를 processor 함수 구현에 직접 적용한다.

## 1. 이미지 업로드/저장 (`io.py`)

- **열기**: `Image.open(path)` 후 반드시 `ImageOps.exif_transpose(img)` 적용 — 스마트폰 사진의 EXIF 회전 정보를 반영해 미리보기와 실제 방향을 일치시킨다
- **RGBA 처리**: PNG 등 알파 채널이 있는 이미지는 `img.convert("RGBA")`로 통일 후, JPG로 저장할 때만 `convert("RGB")` (흰 배경 합성)
- **저장 품질**: JPG `save(path, quality=90, optimize=True)`, PNG `save(path, optimize=True)`, WEBP `save(path, quality=90, method=6)`
- **지원 포맷 검증**: `Image.registered_extensions()`로 확장자 검증 후 미지원 시 명확한 예외

## 2. 크기 조절 (`resize.py`)

- **비율 고정**: 목표 width만 주어지면 `height = int(orig_h * target_w / orig_w)`로 계산
- **리샘플링**: 축소는 `Image.LANCZOS`, 확대(간단 확대)는 `Image.LANCZOS` 또는 `Image.BICUBIC`
- **프리셋 예시**: 인스타그램 정사각(1080x1080), 스토리(1080x1920), 인쇄용 4x6인치(300dpi 기준 1200x1800)
- **크롭 리사이즈**: 비율이 다른 목표 크기는 `ImageOps.fit(img, size, Image.LANCZOS, centering=(0.5, 0.5))` 로 중앙 크롭 후 리사이즈

## 3. 품질 개선 (`quality.py`)

- **노이즈 제거**: `cv2.fastNlMeansDenoisingColored(img_bgr, None, h=10, hColor=10, templateWindowSize=7, searchWindowSize=21)` — `h` 값이 클수록 노이즈는 줄지만 디테일도 손실되므로 5~15 범위 권장
- **선명도(Unsharp Mask)**:
  ```
  blurred = cv2.GaussianBlur(img, (0, 0), sigmaX=3)
  sharpened = cv2.addWeighted(img, 1.5, blurred, -0.5, 0)
  ```
  또는 간단히 `ImageEnhance.Sharpness(img).enhance(1.5)`
- **업스케일**: `cv2.dnn_superres`의 `DnnSuperResImpl_create()` + `readModel("EDSR_x2.pb")` + `setModel("edsr", 2)`. 모델 파일이 없으면 `Image.resize((w*2, h*2), Image.LANCZOS)`로 폴백하고 로그에 "업스케일 모델 미탑재, Lanczos 폴백 사용" 기록
- **자동 보정 프리셋**: 히스토그램 평활화가 필요하면 CLAHE(`cv2.createCLAHE(clipLimit=2.0)`)를 L채널(LAB 색공간)에만 적용해 색이 왜곡되지 않게 한다

## 4. 텍스트 오버레이 (`text_overlay.py`)

```
draw = ImageDraw.Draw(img.convert("RGBA"))
font = ImageFont.truetype(font_path, size)
bbox = draw.textbbox((0, 0), text, font=font)
```
- **정렬**: `textbbox`로 텍스트 크기를 구해 중앙/우측 정렬 좌표 계산
- **그림자/외곽선**: 본문 텍스트보다 1~2px 오프셋으로 어두운 색을 먼저 그린 뒤 본문을 그린다 (가독성 확보)
- **회전 텍스트**: 별도 투명 레이어(`Image.new("RGBA", size, (0,0,0,0))`)에 텍스트를 그린 후 `layer.rotate(angle, expand=True)` 하고 원본에 `paste(layer, pos, layer)`로 합성
- **폰트 폴백**: 지정 폰트 로드 실패 시 시스템 기본 폰트(`ImageFont.load_default()`)로 폴백하고 경고 로그

## 5. 보정 (`enhance.py`)

| 조정 항목 | API | 범위 가이드 |
|----------|-----|------------|
| 밝기 | `ImageEnhance.Brightness(img).enhance(factor)` | 0.5~1.5 |
| 대비 | `ImageEnhance.Contrast(img).enhance(factor)` | 0.5~1.5 |
| 채도 | `ImageEnhance.Color(img).enhance(factor)` | 0~2.0 |
| 화이트밸런스 | LAB 색공간에서 A/B 채널 평균을 128로 보정(Gray World 알고리즘) | - |

- **필터 프리셋**: "따뜻하게"(R+, B-), "차갑게"(R-, B+), "빈티지"(채도↓ + 세피아 LUT), "고대비 흑백"(`convert("L")` + Contrast 1.3)은 위 기본 조정을 조합해 구현하고, 각 프리셋을 딕셔너리 상수로 정의한다

## 6. 배경 제거 (`background_removal.py`)

```
from rembg import remove, new_session
session = new_session("u2net")  # 최초 1회 생성 후 재사용 (매 호출마다 생성하면 느림)
result_rgba = remove(input_bytes, session=session)
```
- **세션 재사용**: `new_session`은 앱 시작 시 한 번만 생성해 모듈 전역/싱글톤으로 유지 — 호출마다 생성하면 수 초씩 지연된다
- **배경 교체**: 결과 RGBA의 알파 마스크를 원하는 배경 이미지/단색 위에 `Image.alpha_composite` 로 합성
- **투명 PNG로 저장**: 배경을 없애기만 할 경우 그대로 RGBA PNG 저장
- **경계 다듬기**: 필요 시 알파 채널에 `cv2.GaussianBlur(alpha, (3,3), 0)`로 가장자리 안티에일리어싱

## 7. 프린트용 스케일링 (`printer.py`)

- 이미지 DPI 기준으로 실제 인쇄 크기(mm/inch)를 계산: `print_px = image_px / source_dpi * target_dpi`
- `QPrinter`에 그릴 때는 `QPainter.drawImage(target_rect, qimage, source_rect)`로 종횡비를 유지한 채 페이지에 맞춘다 (UI 레이어 구현은 ui-designer 담당, 여기서는 스케일 계산 함수만 제공)

## 성능 팁

- 미리보기용 실시간 조정(슬라이더)은 원본이 아니라 **축소된 프록시 이미지**(예: 긴 변 800px)에 적용하고, "적용" 시점에만 원본 해상도로 재처리한다
- OpenCV는 BGR, Pillow/Qt는 RGB 순서이므로 상호 변환 시 반드시 `cv2.cvtColor(img, cv2.COLOR_RGB2BGR)` 변환 지점을 명확히 주석/함수명으로 표시한다 (`to_cv`, `to_pil` 헬퍼 권장)
