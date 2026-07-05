# Trans Pro — 프로젝트 로그

이 문서는 프로젝트의 배경, 주요 의사결정, 구현 현황을 기록합니다. **요구사항이나 프로젝트 방향이 바뀔 때마다 이 문서의 "변경 이력" 섹션에 새 항목을 추가합니다.**

## 프로젝트 개요

- **목표**: 포토샵 lite / Picsart 일부 기능을 구현한 Windows용 Python 데스크톱 이미지 편집 프로그램
- **제품명**: Trans Pro (2026-07-05 이전에는 "TransImage Lite"로 불렸음 — 저장소 이름은 하위 호환을 위해 `TransImage_lite` 그대로 유지)
- **원본 요구사항**: [`req_01.md`](req_01.md)
- **저장소**: https://github.com/jaminism/TransImage_lite
- **개발 방식**: `.claude/` 하위 에이전트 팀 하네스(`image-editor-studio`) 설계를 기반으로 구현. 하네스 구조/에이전트 역할은 [`.claude/CLAUDE.md`](.claude/CLAUDE.md) 참고
- **디자인 벤치마킹**: 사용자가 제공한 참고 스크린샷(보라색 다크 테마 이미지 편집 앱, 좌측 편집도구/파일 사이드바 + 우측 크기·회전·색상 속성 패널 구조)을 기준으로 색상/아이콘/레이아웃을 맞춤. 클라우드 업로드·최근 작업 갤러리·레이어 시스템·알림 등 계정/클라우드 기반 기능은 로컬 단일 이미지 편집기 범위를 벗어나 제외

## 기술 스택 및 의사결정 기록

| 항목 | 결정 | 이유 |
|------|------|------|
| GUI | PySide6 (Qt6) | 네이티브 성능, `QGraphicsView` 캔버스, `QtPrintSupport` 내장 |
| Python 인터프리터 | 비-Anaconda 공식 CPython **3.11.9** (64bit) | Anaconda Python 3.13.5로 `.venv`를 만들면 `PySide6` import 시 `DLL load failed (WinError 127)` 발생. Anaconda3 루트에 있는 자체 vcruntime/msvcp 번들이 Qt6 DLL과 충돌하는 것으로 추정. 비-Anaconda 3.11로 전환해 해결 |
| 이미지 처리(기본) | Pillow | 리사이즈/텍스트/보정/회전/반전 |
| 이미지 처리(고급) | `opencv-python-headless` (`opencv-python` 아님) | 일반 `opencv-python`은 자체 Qt 바인딩을 번들링해서 PySide6와 같은 프로세스에서 충돌 가능 → headless 버전으로 회피 |
| 배경 제거 | `rembg[cpu]` + `onnxruntime` | `rembg`만 설치하면 CPU 백엔드(onnxruntime)가 없어 런타임 에러 발생 → `[cpu]` extra로 설치 |
| 테마 | 커스텀 QSS 다크 테마 + 보라색 액센트 (`src/resources/themes/dark.qss`) | 참고 디자인의 색상(보라색 `#7c5cff`)을 반영. `PySide6-Fluent-Widgets` 대신 순수 PySide6로 구현해 의존성 최소화 |
| 아이콘 | 자체 제작 SVG 라인 아이콘 세트 + `QSvgRenderer`로 직접 래스터화 (`src/app/icons.py`) | 이 환경의 PySide6 배포판은 `imageformats/qsvg.dll`(QPixmap의 svg 로딩) 플러그인이 등록되지 않아 `QIcon(path)`/`QPixmap(path)`가 항상 null을 반환함. `QtSvg.QSvgRenderer` + `QPainter`로 직접 그리는 방식은 플러그인 시스템을 우회하므로 정상 동작 — PyInstaller 배포 시에도 더 안전함 |
| 테스트 | pytest + pytest-qt | 코어 로직(순수 함수) 단위 테스트 + Qt UI/비동기 워커 통합 테스트 |
| 폰트 선택 | `QFontComboBox` + Windows 레지스트리 조회(`core/processors/fonts.py`) | PIL의 `ImageFont.truetype()`은 family 이름이 아니라 실제 파일 경로가 필요 → `HKLM\...\CurrentVersion\Fonts`에서 family→파일 매핑을 조회. 사용자가 직접 추가한 폰트는 `QFontDatabase.addApplicationFont()`로 등록하고 원본 파일 경로를 별도로 기억해둠 |
| 대용량 이미지 지우개 | 축소 프록시(최대 1600px)에서 실시간 편집, 스트로크 종료 시 1회만 원본 해상도 반영 | 1억+ 픽셀 사진에서 마우스 이동마다 풀해상도 QImage 변환을 하면 변환 1회에 수백MB가 필요해 `MemoryError` 발생 → 축소 프록시 방식으로 해결 |

## 구현 현황

| 기능 | 상태 | 비고 |
|------|------|------|
| 이미지 업로드/저장 | ✅ | PNG/JPG/BMP/WEBP, EXIF 회전 보정 |
| 크기 조절 / 회전 / 반전 | ✅ | 자유/비율고정 리사이즈 + SNS·인쇄 프리셋, 90도 좌우 회전, 좌우/상하 반전 |
| 품질 개선 | ✅ | 노이즈 제거, 선명도, 업스케일(모델 없으면 Lanczos 폴백). 비동기(QThread) 처리 + 캔버스 진행 오버레이 |
| 텍스트 추가 | ✅ | 캔버스 위 드래그 가능한 오버레이로 위치를 정한 뒤 적용. 시스템 폰트 선택 + 커스텀 폰트 파일 추가 지원 |
| 보정 | ✅ | 밝기/대비/채도 슬라이더(디바운스 미리보기) + 필터 프리셋. "초기화"는 이 도구에 들어왔을 때 상태로 실제로 되돌림(적용 이미 커밋된 것도 포함) |
| 배경 제거 | ✅ | rembg(u2net), 단색 배경 채우기 지원. 비동기 처리 |
| 지우개 | ✅ | 캔버스에서 마우스 드래그로 알파 채널을 지움. 스트로크(누름→뗌) 단위로 Undo 스택에 반영 |
| 저장 / 다른 이름으로 저장 | ✅ | "저장"은 열린 파일 경로에 덮어쓰기, "다른 이름으로 저장"은 다이얼로그 후 경로 갱신 |
| 인쇄 | ✅ | QPrinter/QPrintDialog — **실제 프린터로 자동 테스트는 못 함**, 사용자 수동 확인 필요 |
| Undo/Redo | ✅ | Ctrl+Z / Ctrl+Y |
| 전체 초기화 | ✅ | 확인 후 원본 이미지로 복귀(되돌리기 가능한 형태로 커밋) |
| 모던 UI | ✅ | 보라색 액센트 다크 테마, 사이드바(편집 도구/파일 그룹) + 캔버스 + 속성 패널 + 상단 툴바, 아이콘 전체 적용 |
| PyInstaller 패키징 | ✅ | `build.spec` + `scripts/build.bat`, onefile 방식(`TransPro.exe`), 실행 스모크 테스트 통과 |

발견 및 수정한 버그:
- `ImageEnhance`(Pillow)가 RGBA 이미지의 알파 채널까지 다른 채널과 함께 블렌딩해서, 배경 제거 후 밝기/대비/채도를 조정하면 투명 영역이 부분적으로 불투명해지는 문제 → `core/processors/enhance.py`에서 알파 채널을 분리했다가 재합성하도록 수정
- 보정 패널의 "초기화" 버튼이 슬라이더 UI만 되돌리고 이미 "적용"으로 커밋된 조정은 되돌리지 못하던 문제 → 도구 진입 시점의 이미지를 baseline으로 기록해두고, 초기화 시 그 baseline으로 실제로 복귀하도록 수정(Undo 가능한 형태로)

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

## 애플리케이션 실행파일(.exe) 빌드

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-build.txt
scripts\build.bat
```

- `build.spec` — PyInstaller onefile 스펙. `rembg`/`onnxruntime`은 `collect_all()`로 네이티브 바이너리까지 수집, 아이콘은 `src/resources/icons/app.ico`
- 산출물: `dist\TransPro.exe` (약 213MB, onnxruntime/opencv/Qt 포함이라 용량이 큼)
- u2net 모델은 exe에 포함하지 않음 — 최초 실행 시 다운로드

## 다음 단계 / TODO

- [ ] (필요 시) 실제 프린터 환경에서 프린트 기능 수동 검증
- [ ] (필요 시) 클린 Windows 환경(Python 미설치)에서 배포용 exe 실행 검증
- [ ] (필요 시) headless(offscreen) 렌더링 환경에 폰트 등록 — 현재 오프스크린 스모크 테스트/스크린샷에서는 폰트가 전혀 없어 텍스트가 빈 사각형으로 렌더링됨(실제 Windows 데스크톱 실행 시에는 시스템 폰트가 정상 사용되어 문제 없음)

## 변경 이력

### 2026-07-05
- Git 저장소 초기화, GitHub(`jaminism/TransImage_lite`) 원격 연결 및 최초 push
- `.claude/` 에이전트 팀 하네스(`image-editor-studio`) 구성 — architect, ui-designer, imaging-engineer, qa-engineer, build-packager + 확장 스킬 2개
- 프로젝트 뼈대 + 실행 가능한 최소 PySide6 앱 스캐폴드 작성
- 핵심 기능 전체 구현: 리사이즈, 보정, 품질 개선, 텍스트 추가, 배경 제거, 프린트, 저장, Undo/Redo, 다크 테마
- 단위/통합 테스트 42개 작성 및 통과, 실제 이미지로 전체 파이프라인 end-to-end 검증(rembg 실제 모델 포함)
- 버그 수정: `ImageEnhance` 알파 채널 보존 문제
- 본 문서(`PROJECT_LOG.md`) 생성 — 이후 요구사항/변경 사항을 이 섹션에 계속 기록하기로 함
- PyInstaller 패키징 완료: `build.spec`, `scripts/build.bat`, 앱 아이콘 생성, `dist\TransImageLite.exe` 빌드 후 헤드리스 실행으로 정상 기동 확인 (실제 프린터/클린 환경 검증은 미완료)
- **사용자 피드백 11건 반영** (버그 2건 + 신규/변경 기능 9건):
  1. 보정 패널 "초기화" 버그 수정 (baseline 복귀 방식으로 재구현)
  2. 텍스트 추가 시 캔버스 위에서 마우스로 드래그해 위치 조정 가능하도록 변경 (`QGraphicsSimpleTextItem` 오버레이)
  3. 프로그램 이름을 "Trans Pro"로 변경 (윈도우 타이틀, 앱 아이콘, exe 이름 등 전체 반영)
  4. 사용자가 제공한 참고 이미지(`IMG_9186.png`, 보라색 다크 테마 이미지 편집 앱)를 벤치마킹해 사이드바(편집 도구/파일 그룹) + 우측 속성 패널 + 상단 툴바 구조와 색상 테마로 리디자인
  5. "전체 초기화" 버튼 추가 (원본 이미지로 복귀, 확인 다이얼로그 포함)
  6. 회전(90도 좌/우) 및 좌우/상하 반전 기능 추가 (`core/processors/transform.py`)
  7. 품질 개선(노이즈 제거/선명도/업스케일) 실행 중 캔버스에 반투명 오버레이 + 진행률 표시줄 + 안내 문구 표시
  8. 지우개 도구 추가 (브러시 크기 조절, 마우스 드래그로 알파 채널 지우기)
  9. "저장"(열린 경로에 덮어쓰기)과 "다른 이름으로 저장"을 분리, 인쇄 버튼을 사이드바/툴바에 눈에 띄게 배치
  10. 인쇄 기능 노출 강화 (기존 기능을 사이드바 액션 + 툴바 아이콘으로 재배치)
  11. 자체 제작 SVG 라인 아이콘 세트(20종)를 사이드바/툴바/버튼 전반에 적용
  - 위 작업 중 PySide6의 svg 이미지 플러그인이 이 환경에서 동작하지 않는 것을 발견 → `QSvgRenderer` 직접 래스터화 방식으로 우회 (`src/app/icons.py`)
  - 신규 테스트 21개 추가(회전/반전, 아이콘 로딩, 사이드바 액션 라우팅, 저장/다른이름저장, 전체초기화, 텍스트 드래그, 지우개, 보정 초기화, 진행 오버레이), 전체 63개 테스트 통과
- **2차 사용자 피드백 6건 반영**:
  1. 상단 툴바 아이콘 툴팁이 흰 배경에 흰 글씨로 안 보이던 문제 → `QToolTip` QSS 스타일 추가(어두운 배경 + 보라색 테두리)
  2. 텍스트 추가 도구에 폰트 선택(`QFontComboBox`) + "폰트 추가..." 버튼(사용자가 가진 .ttf/.otf 파일을 직접 등록) 추가. `core/processors/fonts.py`로 Windows 레지스트리에서 family→파일 경로를 해석해 PIL 렌더링에도 실제로 반영되게 함
  3. 텍스트 패널의 "크기" 스핀박스에서 입력/버튼 클릭이 잘 안 되던 문제 → 원인은 `QSpinBox`를 스타일링할 때 `::up-button`/`::down-button` 서브컨트롤을 지정하지 않아 Qt가 버튼 클릭 영역을 제대로 못 잡던, 잘 알려진 QSS 이슈. 서브컨트롤 위치/크기를 명시해 해결
  4. 텍스트 "적용"이 안 되던 문제 → 텍스트가 비어있을 때 아무 반응 없이 조용히 무시되던 코드가 원인 중 하나로 보여, 항상 신호를 보내고 MainWindow가 "텍스트를 입력해주세요" 안내를 띄우도록 변경. 적용 성공 시에도 상태바에 "텍스트가 추가되었습니다" 메시지 추가
  5. 지우개 사용 시 `DecompressionBombWarning` 이후 `MemoryError` 발생 → 원인은 고해상도(1억+ 픽셀) 사진에서 마우스 이동마다 원본 해상도 그대로 QImage 변환을 시도했기 때문. 축소 프록시(최대 1600px)에서 실시간 편집하고 스트로크 종료 시 1회만 원본 해상도에 반영하도록 재설계. `Image.MAX_IMAGE_PIXELS = None`으로 경고도 제거. 실제 1억 2천만 픽셀 이미지로 재현 테스트해 정상 동작 확인(약 0.9초 로드, 지우기 60회 약 0.5초, 커밋 0.24초)
  6. 좌측 상단에 앱 아이콘 + "Trans Pro" 텍스트 브랜딩 추가 (툴바 맨 앞)
  - 신규 테스트 8개 추가(폰트 경로 해석, 실제 버튼 클릭을 통한 텍스트 적용, 대용량 이미지 지우개 프록시/커밋), 전체 68개 테스트 통과
