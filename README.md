# Trans Pro

Windows용 경량 이미지 편집 데스크톱 앱 (포토샵 lite / Picsart 스타일). 구 프로젝트명 TransImage Lite — 저장소 이름은 하위 호환을 위해 유지합니다.

## 기능

- [x] 이미지 업로드
- [x] 크기 조절 (자유/비율고정, SNS·인쇄 프리셋) / 회전(90도 좌우) / 좌우·상하 반전
- [x] 품질 개선 (노이즈 제거, 선명도, 업스케일) — 처리 중 캔버스에 진행 오버레이 표시
- [x] 텍스트 추가 — 캔버스에서 마우스로 드래그해 위치를 정한 뒤 적용
- [x] 보정 (밝기/대비/채도, 필터 프리셋) — 초기화 시 이 도구에 들어왔을 때 상태로 복귀
- [x] 배경 제거 (rembg, 단색 배경 채우기)
- [x] 지우개 (브러시 드래그로 알파 채널 지우기)
- [x] 저장(덮어쓰기) / 다른 이름으로 저장 (PNG/JPEG/WEBP/BMP)
- [x] 인쇄
- [x] Undo/Redo, 전체 초기화(원본으로 복귀)
- [x] 모던 다크 + 보라색 액센트 테마, 아이콘 기반 사이드바/툴바

## 화면 구성

좌측 사이드바(편집 도구 / 파일 그룹), 중앙 캔버스, 우측 속성 패널, 상단 툴바, 하단 상태바로 구성됩니다. 사용자가 제공한 참고 디자인(보라색 다크 테마의 이미지 편집 앱)을 벤치마킹해 색상/아이콘/레이아웃을 맞췄습니다. 클라우드 업로드·최근 작업 갤러리·레이어 시스템 등 계정/클라우드 기반 기능은 로컬 단일 이미지 편집기 범위를 벗어나 포함하지 않았습니다.

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

## Windows 실행파일(.exe) 빌드

```
.venv\Scripts\python.exe -m pip install -r requirements-build.txt
scripts\build.bat
```

`dist\TransPro.exe` 하나로 배포되는 단일 실행파일이 생성됩니다 (PyInstaller `--onefile` 방식, `build.spec` 참고). 배경 제거용 u2net 모델은 exe에 포함되지 않고 최초 실행 시 다운로드됩니다.

## 프로젝트 구조

```
src/
├── main.py                  # 앱 진입점, 다크 테마/아이콘 로드
├── app/                      # UI 레이어 (PySide6)
│   ├── main_window.py        # 메인 윈도우 (사이드바 / 캔버스 / 속성 패널 / 툴바)
│   ├── canvas_widget.py       # 캔버스 (줌/팬, 텍스트 드래그 오버레이, 지우개, 진행 오버레이)
│   ├── icons.py               # SVG 아이콘 로더 (QSvgRenderer 직접 래스터화)
│   └── panels/                # 도구별 속성 패널
│       ├── resize_panel.py     # 크기 조절 + 회전/반전
│       ├── enhance_panel.py    # 보정 (초기화 시 baseline 복귀)
│       ├── quality_panel.py
│       ├── text_panel.py       # 텍스트 (드래그 위치는 캔버스가 소유)
│       ├── background_panel.py
│       └── erase_panel.py      # 지우개 브러시 크기
├── core/                     # 이미지 처리 로직 (Qt 비의존, 순수 함수)
│   ├── image_document.py      # Undo/Redo 상태 관리
│   └── processors/
│       ├── io.py
│       ├── resize.py
│       ├── enhance.py
│       ├── quality.py
│       ├── text_overlay.py
│       ├── background_removal.py
│       ├── transform.py        # 회전/반전
│       └── printer.py
├── workers/
│   └── async_tasks.py         # QThread 기반 비동기 처리 워커
└── resources/
    ├── themes/dark.qss         # 모던 다크 + 보라색 액센트 테마
    └── icons/                  # SVG 라인 아이콘 세트 + 앱 아이콘(app.ico)

tests/
├── core/                      # processor 단위 테스트
└── app/                       # Qt UI 통합 테스트 (pytest-qt)
```

## 하네스

이 프로젝트는 `.claude/` 하위 에이전트 팀 하네스(`image-editor-studio`)로 개발됩니다. 구조와 사용법은 [`.claude/CLAUDE.md`](.claude/CLAUDE.md) 참고.

## 요구사항 문서

원본 요구사항은 [`req_01.md`](req_01.md) 참고.

## 프로젝트 로그

배경, 기술 스택 의사결정, 구현 현황, 변경 이력은 [`PROJECT_LOG.md`](PROJECT_LOG.md)에서 계속 관리합니다.
