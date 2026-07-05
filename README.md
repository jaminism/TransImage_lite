# TransImage Lite

Windows용 경량 이미지 편집 데스크톱 앱 (포토샵 lite / Picsart 스타일).

## 기능

- [x] 이미지 업로드
- [x] 크기 조절 (자유/비율고정, SNS·인쇄 프리셋)
- [x] 품질 개선 (노이즈 제거, 선명도, 업스케일)
- [x] 텍스트 추가 (폰트 크기/색상/회전/그림자)
- [x] 보정 (밝기/대비/채도, 필터 프리셋)
- [x] 배경 제거 (rembg, 단색 배경 채우기)
- [x] 프린트 출력
- [x] 이미지 다운로드 (PNG/JPEG/WEBP/BMP)
- [x] Undo/Redo

## 개발 환경

- Python 3.11+ (Anaconda가 아닌 표준 CPython 권장 — PySide6 DLL 충돌 회피)
- PySide6 (Qt6) — UI
- Pillow, OpenCV(headless) — 이미지 처리
- rembg[cpu] (onnxruntime) — 배경 제거

## 시작하기

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

배경 제거 기능은 최초 실행 시 u2net 모델(약 176MB)을 `~/.u2net`에 자동 다운로드합니다.

## 테스트

```
pip install -r requirements-dev.txt
set QT_QPA_PLATFORM=offscreen   # 헤드리스 환경에서 UI 테스트 실행 시
pytest
```

## 프로젝트 구조

```
src/
├── main.py                  # 앱 진입점, 다크 테마 로드
├── app/                      # UI 레이어 (PySide6)
│   ├── main_window.py        # 메인 윈도우 (툴 사이드바 / 캔버스 / 속성 패널)
│   ├── canvas_widget.py       # 이미지 캔버스 (QGraphicsView 기반, 줌/팬)
│   └── panels/                # 도구별 속성 패널
│       ├── resize_panel.py
│       ├── enhance_panel.py
│       ├── quality_panel.py
│       ├── text_panel.py
│       ├── background_panel.py
│       └── export_panel.py
├── core/                     # 이미지 처리 로직 (Qt 비의존, 순수 함수)
│   ├── image_document.py      # Undo/Redo 상태 관리
│   └── processors/
│       ├── io.py
│       ├── resize.py
│       ├── enhance.py
│       ├── quality.py
│       ├── text_overlay.py
│       ├── background_removal.py
│       └── printer.py
├── workers/
│   └── async_tasks.py         # QThread 기반 비동기 처리 워커
└── resources/themes/dark.qss  # 모던 다크 테마

tests/
├── core/                      # processor 단위 테스트
└── app/                       # Qt UI 통합 테스트 (pytest-qt)
```

## 하네스

이 프로젝트는 `.claude/` 하위 에이전트 팀 하네스(`image-editor-studio`)로 개발됩니다. 구조와 사용법은 [`.claude/CLAUDE.md`](.claude/CLAUDE.md) 참고.

## 요구사항 문서

원본 요구사항은 [`req_01.md`](req_01.md) 참고.
