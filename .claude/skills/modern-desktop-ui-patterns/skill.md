---
name: modern-desktop-ui-patterns
description: "PySide6 기반 모던 데스크톱 UI 패턴 라이브러리. Fluent Design 테마, 캔버스(QGraphicsView) 패턴, 반응형 3단 레이아웃, 비동기 워커 연동, 다크/라이트 테마 전환을 제공하는 ui-designer 확장 스킬. '모던 UI', 'Fluent Design', 'PySide6 테마', '캔버스 줌/팬', '다크모드', '비동기 UI 업데이트' 등 데스크톱 앱 UI 구현 시 사용한다. 단, 실제 이미지 처리 알고리즘 구현은 이 스킬의 범위가 아니다."
---

# Modern Desktop UI Patterns — PySide6 모던 UI 패턴

ui-designer 에이전트가 활용하는 PySide6 레이아웃, 테마, 컴포넌트, 비동기 연동 패턴 레퍼런스.

## 대상 에이전트

`ui-designer` — 이 스킬의 패턴을 화면 구현에 직접 적용한다.

## 1. 모던 룩앤필 확보 전략

| 방법 | 적용 |
|------|------|
| Fluent Design 위젯 | `PySide6-Fluent-Widgets` (`qfluentwidgets`) 사용 — `PushButton`, `CardWidget`, `SwitchButton`, `Slider` 등이 기본 제공 |
| 다크 테마 기본값 | `setTheme(Theme.DARK)` 로 시작, 사용자가 라이트로 전환 가능하게 토글 제공 |
| 카드형 레이아웃 | 툴 패널을 `CardWidget`으로 감싸 그림자/라운드 코너 적용 |
| 여백/타이포 일관성 | 8px 그리드 기반 spacing(8/16/24), 제목 16~20px / 본문 13~14px |
| 아이콘 | `qfluentwidgets.FluentIcon` 또는 SVG 아이콘 세트 사용, 단색 라인 아이콘으로 통일 |

QFluentWidgets를 쓰지 않는 경우, 순수 QSS로도 유사한 느낌을 낼 수 있다: 다크 배경(#1e1e1e~#2b2b2b), 액센트 컬러 1개(예: #4cc2ff), 버튼 라운드(`border-radius: 6px`), hover 시 밝기 전환 애니메이션.

## 2. 3단 레이아웃 골격

```
QMainWindow
└── QWidget (central)
    └── QHBoxLayout
        ├── ToolSidebar (QListWidget/QToolBar, 고정폭 64~72px, 아이콘만)
        ├── CanvasArea (QGraphicsView, stretch=1)
        └── PropertiesPanel (QStackedWidget, 고정폭 280~320px)
```

- **ToolSidebar**: 아이콘 클릭 시 `PropertiesPanel`의 `QStackedWidget.setCurrentIndex()`로 해당 도구 패널 전환
- **CanvasArea**: `stretch=1`로 남은 공간을 모두 차지, 창 리사이즈에 반응
- **PropertiesPanel**: 도구가 선택되지 않으면 빈 상태(empty state) 안내 표시

## 3. 캔버스 (QGraphicsView) 패턴

```
scene = QGraphicsScene()
pixmap_item = QGraphicsPixmapItem(QPixmap.fromImage(qimage))
scene.addItem(pixmap_item)
view = QGraphicsView(scene)
view.setRenderHint(QPainter.SmoothPixmapTransform)
view.setDragMode(QGraphicsView.ScrollHandDrag)  # 팬
```
- **줌**: `wheelEvent`에서 `view.scale(factor, factor)`, Ctrl+휠로 줌 vs 일반 휠로 스크롤 구분
- **줌 맞춤**: "화면에 맞추기" 버튼은 `view.fitInView(pixmap_item, Qt.KeepAspectRatio)`
- **전/후 비교**: `pixmap_item.setPixmap()`을 토글하거나, 화면을 절반으로 나눠 원본/편집본을 동시에 표시하는 `QSplitter` 옵션 제공
- **PIL → Qt 변환**: `ImageQt.ImageQt(pil_image)` (Pillow의 `PIL.ImageQt` 모듈) 로 `QImage` 생성 후 `QPixmap.fromImage()`

## 4. 비동기 처리 연동 (UI 논블로킹)

무거운 처리(품질 개선, 배경 제거)는 반드시 워커 스레드에서 실행하고 결과를 시그널로 받는다:

```
class ProcessWorker(QThread):
    finished = Signal(object)   # 처리된 PIL.Image
    error = Signal(str)

    def __init__(self, fn, **kwargs):
        super().__init__()
        self.fn, self.kwargs = fn, kwargs

    def run(self):
        try:
            result = self.fn(**self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
```
- 버튼 클릭 시: 진행률/스피너 표시 → `worker.start()` → `finished`/`error` 시그널에서 캔버스 업데이트 및 스피너 해제
- 사용자가 처리 중 다른 조작을 하지 못하도록 관련 컨트롤을 `setEnabled(False)` 했다가 완료 시 복원

## 5. 슬라이더 실시간 미리보기 + 디바운스

```
self.debounce_timer = QTimer(singleShot=True)
slider.valueChanged.connect(lambda: self.debounce_timer.start(150))
self.debounce_timer.timeout.connect(self.apply_preview)
```
- 슬라이더를 움직이는 동안은 축소된 프록시 이미지로 미리보기만 갱신 (150ms 디바운스)
- 슬라이더를 놓으면(`sliderReleased`) 원본 해상도로 최종 반영

## 6. 색/텍스트 컨트롤

- **컬러 피커**: `QColorDialog.getColor()` 또는 QFluentWidgets `ColorPickerButton`
- **폰트 선택**: `QFontComboBox` + 크기 `QSpinBox`
- **알림/토스트**: `qfluentwidgets.InfoBar` 로 저장 완료/에러 메시지를 비침습적으로 표시 (모달 다이얼로그 남용 금지)

## 7. 단축키/메뉴

| 단축키 | 동작 | 구현 |
|--------|------|------|
| Ctrl+O | 열기 | `QShortcut(QKeySequence.Open, ...)` |
| Ctrl+S | 저장 | `QKeySequence.Save` |
| Ctrl+Z / Ctrl+Y | 실행취소/다시실행 | `QKeySequence.Undo` / `Redo` |
| Ctrl+P | 프린트 | `QKeySequence.Print` |
| Ctrl+ / Ctrl- | 줌 인/아웃 | `QKeySequence.ZoomIn` / `ZoomOut` |

## 8. 접근성/견고성 체크리스트

- [ ] 모든 아이콘 버튼에 `setToolTip()` 제공
- [ ] 키보드만으로 주요 도구 접근 가능 (Tab 순서 확인)
- [ ] 로딩 중 상태를 시각적으로 명확히 표시 (스피너/프로그레스바)
- [ ] 창 최소 크기 지정으로 레이아웃 깨짐 방지 (`setMinimumSize`)
- [ ] 고DPI 대응 (`Qt.AA_EnableHighDpiScaling`)
