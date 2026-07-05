# Trans Pro

Windows용 경량 이미지 편집 데스크톱 앱 (포토샵 lite / Picsart 스타일). 구 프로젝트명 TransImage Lite — 저장소 이름은 하위 호환을 위해 유지합니다.

## 기능

- [x] 홈 화면 — 첫 실행/이미지를 닫았을 때 환영 문구 + 주요 기능 바로가기 카드 + 최근 작업 목록 표시
- [x] 이미지 업로드 / 닫기 (닫으면 홈 화면으로 복귀)
- [x] 크기 조절 (자유/비율고정, SNS·인쇄 프리셋) / 회전(90도 좌우, 각도 직접 입력) / 좌우·상하 반전
- [x] 품질 개선 (노이즈 제거, 선명도, 업스케일) — 처리 중 캔버스에 스캔 라인 + 스파클 애니메이션 오버레이 표시
- [x] 텍스트 추가 — 캔버스에서 마우스로 드래그해 위치를 정한 뒤 적용(미리보기와 최종 결과가 완전히 동일하게 렌더링됨), 시스템 폰트 선택 + 커스텀 폰트 파일 추가 + 한글 미지원 폰트만 자동 대체(지원하는 폰트는 선택한 그대로 적용), 굵게/기울임 옵션, 크기는 이미지 해상도 대비 %(해상도가 달라져도 항상 같은 비율), 전용 초기화 버튼(적용된 텍스트도 되돌림)
- [x] 보정 (밝기/대비/채도, 필터 프리셋) — 초기화 시 이 도구에 들어왔을 때 상태로 복귀
- [x] 배경 제거 (rembg 자동 제거, 단색 배경 채우기) — 원본 크기는 그대로 유지되며, 투명해진 영역은 체커보드로 표시
- [x] 저장(덮어쓰기) / 다른 이름으로 저장 (PNG/JPEG/WEBP/BMP)
- [x] 인쇄
- [x] Undo/Redo, 전체 초기화(원본으로 복귀)
- [x] 상태바 확대/축소 컨트롤 — 축소/확대 버튼, 슬라이더(10~400%), 프리셋 메뉴, 화면에 맞추기 버튼 (Ctrl+휠 줌과도 연동)
- [x] 모던 다크 + 보라색 액센트 테마, 아이콘 기반 사이드바/툴바, 사이드바·캔버스·속성 패널이 둥근 모서리의 독립된 카드로 분리된 레이아웃

## 화면 구성

좌측 사이드바(편집 도구 / 파일 그룹) + 우측 속성 패널 + 상단 툴바 + 하단 상태바는 이미지 유무와 관계없이 항상 표시됩니다. 가운데 영역만 전환되는데, 이미지가 없으면 홈 화면(환영 문구 + 사진 가져오기/빠른 보정/글씨 추가/배경 제거 바로가기 카드 + 최근 작업 목록)을, 이미지를 열면 캔버스를 보여줍니다. 사용자가 제공한 참고 디자인(보라색 다크 테마의 이미지 편집 앱)을 벤치마킹해 색상/아이콘/레이아웃을 맞췄습니다. 클라우드 업로드·QR 업로드·레이어 시스템 등 계정/클라우드 기반 기능은 로컬 단일 이미지 편집기 범위를 벗어나 포함하지 않았습니다(최근 작업 목록은 로컬 설정 파일 기반).

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
│   ├── main_window.py        # 메인 윈도우 (홈/편집 화면 전환, 사이드바 / 캔버스 / 속성 패널 / 툴바)
│   ├── home_widget.py         # 홈 화면 (바로가기 카드 + 최근 작업 목록)
│   ├── canvas_widget.py       # 캔버스 (줌/팬, 텍스트 드래그 오버레이, 진행 오버레이)
│   ├── icons.py               # SVG 아이콘 로더 (QSvgRenderer 직접 래스터화)
│   └── panels/                # 도구별 속성 패널
│       ├── resize_panel.py     # 크기 조절 + 회전/반전
│       ├── enhance_panel.py    # 보정 (초기화 시 baseline 복귀)
│       ├── quality_panel.py
│       ├── text_panel.py       # 텍스트 (드래그 위치는 캔버스가 소유, 크기는 %)
│       └── background_panel.py
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
