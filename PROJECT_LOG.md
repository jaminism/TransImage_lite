# TransImage Lite — 프로젝트 로그

이 문서는 프로젝트의 배경, 주요 의사결정, 구현 현황을 기록합니다. **요구사항이나 프로젝트 방향이 바뀔 때마다 이 문서의 "변경 이력" 섹션에 새 항목을 추가합니다.**

## 프로젝트 개요

- **목표**: 포토샵 lite / Picsart 일부 기능을 구현한 Windows용 Python 데스크톱 이미지 편집 프로그램
- **원본 요구사항**: [`req_01.md`](req_01.md)
- **저장소**: https://github.com/jaminism/TransImage_lite
- **개발 방식**: `.claude/` 하위 에이전트 팀 하네스(`image-editor-studio`) 설계를 기반으로 구현. 하네스 구조/에이전트 역할은 [`.claude/CLAUDE.md`](.claude/CLAUDE.md) 참고

## 기술 스택 및 의사결정 기록

| 항목 | 결정 | 이유 |
|------|------|------|
| GUI | PySide6 (Qt6) | 네이티브 성능, `QGraphicsView` 캔버스, `QtPrintSupport` 내장 |
| Python 인터프리터 | 비-Anaconda 공식 CPython **3.11.9** (64bit) | Anaconda Python 3.13.5로 `.venv`를 만들면 `PySide6` import 시 `DLL load failed (WinError 127)` 발생. Anaconda3 루트에 있는 자체 vcruntime/msvcp 번들이 Qt6 DLL과 충돌하는 것으로 추정. 비-Anaconda 3.11로 전환해 해결 |
| 이미지 처리(기본) | Pillow | 리사이즈/텍스트/보정 |
| 이미지 처리(고급) | `opencv-python-headless` (`opencv-python` 아님) | 일반 `opencv-python`은 자체 Qt 바인딩을 번들링해서 PySide6와 같은 프로세스에서 충돌 가능 → headless 버전으로 회피 |
| 배경 제거 | `rembg[cpu]` + `onnxruntime` | `rembg`만 설치하면 CPU 백엔드(onnxruntime)가 없어 런타임 에러 발생 → `[cpu]` extra로 설치 |
| 테마 | 커스텀 QSS 다크 테마 (`src/resources/themes/dark.qss`) | 아키텍처 문서상 `PySide6-Fluent-Widgets` 후보도 있었으나, 의존성을 늘리지 않고 순수 PySide6로 모던한 룩을 구현 |
| 테스트 | pytest + pytest-qt | 코어 로직(순수 함수) 단위 테스트 + Qt UI/비동기 워커 통합 테스트 |

## 구현 현황

| 기능 | 상태 | 비고 |
|------|------|------|
| 이미지 업로드/저장 | ✅ | PNG/JPG/BMP/WEBP, EXIF 회전 보정 |
| 크기 조절 | ✅ | 자유/비율고정, SNS·인쇄 프리셋 |
| 품질 개선 | ✅ | 노이즈 제거, 선명도, 업스케일(모델 없으면 Lanczos 폴백). 비동기(QThread) 처리 |
| 텍스트 추가 | ✅ | 폰트 크기/색상/회전/그림자 |
| 보정 | ✅ | 밝기/대비/채도 슬라이더(디바운스 미리보기) + 필터 프리셋(따뜻하게/차갑게/빈티지/흑백) |
| 배경 제거 | ✅ | rembg(u2net), 단색 배경 채우기 지원. 비동기 처리 |
| 프린트 출력 | ✅ | QPrinter/QPrintDialog — **실제 프린터로 자동 테스트는 못 함**, 사용자 수동 확인 필요 |
| 다운로드(저장) | ✅ | PNG/JPEG/WEBP/BMP, 품질 조절 |
| Undo/Redo | ✅ | Ctrl+Z / Ctrl+Y |
| 모던 UI | ✅ | 다크 테마, 3단 레이아웃(사이드바/캔버스/속성패널) |
| PyInstaller 패키징 | ⬜ | 예정 |

발견 및 수정한 버그:
- `ImageEnhance`(Pillow)가 RGBA 이미지의 알파 채널까지 다른 채널과 함께 블렌딩해서, 배경 제거 후 밝기/대비/채도를 조정하면 투명 영역이 부분적으로 불투명해지는 문제 발견 → `core/processors/enhance.py`에서 알파 채널을 분리했다가 재합성하도록 수정, 회귀 테스트 추가

## 애플리케이션 실행 방법

```powershell
# 최초 1회: 의존성 설치 (반드시 .venv의 Python 3.11 사용 — Anaconda 아님)
.venv\Scripts\python.exe -m pip install -r requirements.txt

# 실행
.venv\Scripts\python.exe src\main.py
```

- 배경 제거를 처음 사용할 때 u2net 모델(약 176MB)이 `%USERPROFILE%\.u2net`에 자동 다운로드됩니다 (인터넷 연결 필요, 1회만).
- 프린트 기능은 실제 프린터가 없어도 Windows의 "Microsoft Print to PDF"를 프린터로 선택하면 테스트할 수 있습니다.
- 테스트 실행: `.venv\Scripts\python.exe -m pytest` (UI 테스트 포함, headless 환경에서는 `$env:QT_QPA_PLATFORM = "offscreen"` 설정 필요)

## 다음 단계 / TODO

- [ ] PyInstaller로 Windows 실행파일(.exe) 패키징
- [ ] (필요 시) 실제 프린터 환경에서 프린트 기능 수동 검증

## 변경 이력

### 2026-07-05
- Git 저장소 초기화, GitHub(`jaminism/TransImage_lite`) 원격 연결 및 최초 push
- `.claude/` 에이전트 팀 하네스(`image-editor-studio`) 구성 — architect, ui-designer, imaging-engineer, qa-engineer, build-packager + 확장 스킬 2개
- 프로젝트 뼈대 + 실행 가능한 최소 PySide6 앱 스캐폴드 작성
- 핵심 기능 전체 구현: 리사이즈, 보정, 품질 개선, 텍스트 추가, 배경 제거, 프린트, 저장, Undo/Redo, 다크 테마
- 단위/통합 테스트 42개 작성 및 통과, 실제 이미지로 전체 파이프라인 end-to-end 검증(rembg 실제 모델 포함)
- 버그 수정: `ImageEnhance` 알파 채널 보존 문제
- 본 문서(`PROJECT_LOG.md`) 생성 — 이후 요구사항/변경 사항을 이 섹션에 계속 기록하기로 함
