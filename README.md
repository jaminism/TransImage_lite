# TransImage Lite

Windows용 경량 이미지 편집 데스크톱 앱 (포토샵 lite / Picsart 스타일).

## 기능

- [x] 프로젝트 뼈대 / 실행 가능한 최소 앱
- [ ] 이미지 업로드
- [ ] 크기 조절
- [ ] 품질 개선 (노이즈 제거 / 선명도 / 업스케일)
- [ ] 텍스트 추가
- [ ] 보정 (밝기 / 대비 / 채도 / 필터)
- [ ] 배경 제거
- [ ] 프린트 출력
- [ ] 이미지 다운로드

## 개발 환경

- Python 3.11+
- PySide6 (Qt6) — UI
- Pillow, OpenCV — 이미지 처리
- rembg — 배경 제거

## 시작하기

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

## 프로젝트 구조

```
src/
├── main.py              # 앱 진입점
├── app/                 # UI 레이어 (PySide6)
│   ├── main_window.py   # 메인 윈도우 (툴 사이드바 / 캔버스 / 속성 패널)
│   └── canvas_widget.py # 이미지 캔버스 (QGraphicsView 기반)
└── core/                # 이미지 처리 로직 (Qt 비의존)
    ├── image_document.py
    └── processors/       # 기능별 이미지 처리 함수 (구현 예정)
```

## 하네스

이 프로젝트는 `.claude/` 하위 에이전트 팀 하네스(`image-editor-studio`)로 개발됩니다. 구조와 사용법은 [`.claude/CLAUDE.md`](.claude/CLAUDE.md) 참고.

## 요구사항 문서

원본 요구사항은 [`req_01.md`](req_01.md) 참고.
