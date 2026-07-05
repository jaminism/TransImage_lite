from __future__ import annotations

import logging
import os
from pathlib import Path

from PIL import Image
from PIL.ImageQt import ImageQt
from PySide6.QtCore import QSettings, QSize, Qt
from PySide6.QtGui import QAction, QColor, QKeySequence, QPainter, QPixmap
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QSplitter,
    QStackedWidget,
    QToolBar,
    QWidget,
)

from app.canvas_widget import CanvasWidget
from app.home_widget import HomeWidget
from app.icons import icon
from app.panels.background_panel import BackgroundPanel
from app.panels.enhance_panel import EnhancePanel
from app.panels.quality_panel import QualityPanel
from app.panels.resize_panel import ResizePanel
from app.panels.text_panel import TextPanel
from core.image_document import ImageDocument
from core.processors.io import SUPPORTED_EXTENSIONS, open_image, save_image
from core.processors.printer import fit_to_page
from core.processors.text_overlay import add_text
from workers.async_tasks import ProcessWorker

logger = logging.getLogger(__name__)

# properties_panel(QStackedWidget) 페이지 인덱스
PANEL_RESIZE = 0
PANEL_ENHANCE = 1
PANEL_QUALITY = 2
PANEL_TEXT = 3
PANEL_BACKGROUND = 4

TOOL_PANEL_LABELS = ["크기/회전", "보정", "품질 개선", "텍스트", "배경 제거"]

# center_stack(QStackedWidget) 페이지 인덱스 — 홈 화면 vs 캔버스
STACK_HOME = 0
STACK_EDITOR = 1

_QUICK_ACTION_PANEL = {"enhance": PANEL_ENHANCE, "text": PANEL_TEXT, "background": PANEL_BACKGROUND}

_OPEN_FILTER = "이미지 파일 (*.png *.jpg *.jpeg *.bmp *.webp)"
_SAVE_FILTER = "PNG (*.png);;JPEG (*.jpg *.jpeg);;WEBP (*.webp);;BMP (*.bmp)"
_DEFAULT_SAVE_QUALITY = 90
_DEFAULT_TEXT_HEIGHT_HINT = 400
_MAX_RECENT_FILES = 8

_ASYNC_BUSY_LABELS = {
    "denoise": "노이즈 제거 처리 중...",
    "sharpen": "선명도 향상 처리 중...",
    "upscale": "업스케일 처리 중...",
    "remove_background": "배경 제거 처리 중...",
}


class MainWindow(QMainWindow):
    """Trans Pro 메인 윈도우: 홈 화면 / 편집 화면(사이드바 / 캔버스 / 속성 패널)을 전환한다.

    각 편집 패널은 (processor_fn, kwargs, is_async) 형태로 apply_requested를 발생시키고,
    이 윈도우가 ImageDocument에 실제로 반영한다. 무거운 작업은 ProcessWorker로 비동기 실행한다.
    텍스트 도구는 캔버스와 직접 상호작용하므로 전용 시그널로 연결한다.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Trans Pro")
        self.resize(1360, 840)

        self.document = ImageDocument()
        self.canvas = CanvasWidget()
        # 명시적으로 IniFormat을 지정한다 — 2-인자 생성자는 setDefaultFormat()을 따르지
        # 않고 항상 NativeFormat(Windows 레지스트리)을 쓰는 것으로 확인되어(테스트에서
        # 실제 레지스트리를 오염시키는 문제 발견), 테스트에서 QSettings.setPath()로
        # 안전하게 격리할 수 있도록 포맷을 고정한다.
        self._settings = QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope, "TransPro", "TransPro")
        self._worker: ProcessWorker | None = None
        self._current_path: str | None = None
        self._enhance_baseline: Image.Image | None = None
        self._text_baseline: Image.Image | None = None
        self._quality_baseline: Image.Image | None = None
        self._active_panel_index = PANEL_RESIZE
        self._last_tool_row = 0
        self._row_kind: dict[int, str] = {}
        self._tool_rows: dict[int, int] = {}
        self._action_handlers: dict[int, callable] = {}

        self._build_panels()
        self._build_layout()
        self._build_menu_and_toolbar()
        self._build_status_bar()
        self._update_actions_enabled()
        self._load_recent_files()

    # ------------------------------------------------------------------ UI 구성
    def _build_panels(self) -> None:
        self.home_widget = HomeWidget()
        self.home_widget.open_requested.connect(self._open_image)
        self.home_widget.quick_action_requested.connect(self._on_home_quick_action)
        self.home_widget.recent_file_opened.connect(self._open_path)

        self.resize_panel = ResizePanel()
        self.enhance_panel = EnhancePanel()
        self.quality_panel = QualityPanel()
        self.text_panel = TextPanel()
        self.background_panel = BackgroundPanel()

        self._panels = [
            self.resize_panel,
            self.enhance_panel,
            self.quality_panel,
            self.text_panel,
            self.background_panel,
        ]

        for panel in self._panels:
            if hasattr(panel, "preview_requested"):
                panel.preview_requested.connect(self._on_preview_requested)
            if hasattr(panel, "apply_requested"):
                panel.apply_requested.connect(self._on_apply_requested)

        self.enhance_panel.reset_requested.connect(self._on_enhance_reset)
        self.text_panel.overlay_changed.connect(self._on_text_overlay_changed)
        self.text_panel.text_apply_requested.connect(self._on_text_apply)
        self.text_panel.reset_requested.connect(self._on_text_reset)

    def _build_layout(self) -> None:
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(190)
        self.sidebar.setIconSize(QSize(20, 20))

        self._add_sidebar_header("편집 도구")
        self._add_sidebar_tool("크기 / 회전", "resize", PANEL_RESIZE)
        self._add_sidebar_tool("보정", "enhance", PANEL_ENHANCE)
        self._add_sidebar_tool("품질 개선", "quality", PANEL_QUALITY)
        self._add_sidebar_tool("텍스트 추가", "text", PANEL_TEXT)
        self._add_sidebar_tool("배경 제거", "background_remove", PANEL_BACKGROUND)
        self._add_sidebar_header("파일")
        self._add_sidebar_action("저장", "save", self._on_quick_save)
        self._add_sidebar_action("다른 이름으로 저장", "save_as", self._on_save_as)
        self._add_sidebar_action("인쇄", "print", self._on_print)

        self.sidebar.currentRowChanged.connect(self._on_sidebar_row_changed)

        self.properties_panel = QStackedWidget()
        for panel in self._panels:
            self.properties_panel.addWidget(panel)
        self.properties_panel.setFixedWidth(320)

        # 사이드바/속성 패널은 이미지 유무와 상관없이 항상 보인다 — 가운데 영역(홈 화면 vs
        # 캔버스)만 전환한다. 이렇게 하면 이미지를 열기 전에도 어떤 도구들이 있는지 보이고,
        # 도구를 먼저 눌러둔 채로 사진을 나중에 가져올 수도 있다.
        self.center_stack = QStackedWidget()
        self.center_stack.addWidget(self.home_widget)  # STACK_HOME
        self.center_stack.addWidget(self.canvas)  # STACK_EDITOR

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.sidebar)
        splitter.addWidget(self.center_stack)
        splitter.addWidget(self.properties_panel)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)

        self.sidebar.setCurrentRow(1)  # 첫 번째 실제 도구("크기 / 회전")

    def _add_sidebar_header(self, text: str) -> None:
        item = QListWidgetItem(text)
        item.setFlags(Qt.ItemFlag.NoItemFlags)
        item.setForeground(QColor("#8b8fa3"))
        font = item.font()
        font.setBold(True)
        font.setPointSize(max(8, font.pointSize() - 1))
        item.setFont(font)
        self.sidebar.addItem(item)

    def _add_sidebar_tool(self, label: str, icon_name: str, panel_index: int) -> None:
        item = QListWidgetItem(icon(icon_name), label)
        self.sidebar.addItem(item)
        row = self.sidebar.count() - 1
        self._row_kind[row] = "tool"
        self._tool_rows[row] = panel_index

    def _add_sidebar_action(self, label: str, icon_name: str, handler) -> None:
        item = QListWidgetItem(icon(icon_name), label)
        self.sidebar.addItem(item)
        row = self.sidebar.count() - 1
        self._row_kind[row] = "action"
        self._action_handlers[row] = handler

    def _build_menu_and_toolbar(self) -> None:
        file_menu = self.menuBar().addMenu("파일")

        self.open_action = QAction(icon("open"), "열기...", self)
        self.open_action.setShortcut(QKeySequence.Open)
        self.open_action.triggered.connect(self._open_image)
        file_menu.addAction(self.open_action)

        self.close_action = QAction(icon("close"), "닫기", self)
        self.close_action.setShortcut(QKeySequence.Close)
        self.close_action.triggered.connect(self._on_close_image)
        file_menu.addAction(self.close_action)

        self.save_action = QAction(icon("save"), "저장", self)
        self.save_action.setShortcut(QKeySequence.Save)
        self.save_action.triggered.connect(self._on_quick_save)
        file_menu.addAction(self.save_action)

        self.save_as_action = QAction(icon("save_as"), "다른 이름으로 저장...", self)
        self.save_as_action.setShortcut(QKeySequence.SaveAs)
        self.save_as_action.triggered.connect(self._on_save_as)
        file_menu.addAction(self.save_as_action)

        self.print_action = QAction(icon("print"), "인쇄...", self)
        self.print_action.setShortcut(QKeySequence.Print)
        self.print_action.triggered.connect(self._on_print)
        file_menu.addAction(self.print_action)

        edit_menu = self.menuBar().addMenu("편집")

        self.undo_action = QAction(icon("undo"), "실행 취소", self)
        self.undo_action.setShortcut(QKeySequence.Undo)
        self.undo_action.triggered.connect(self._on_undo)
        edit_menu.addAction(self.undo_action)

        self.redo_action = QAction(icon("redo"), "다시 실행", self)
        self.redo_action.setShortcut(QKeySequence.Redo)
        self.redo_action.triggered.connect(self._on_redo)
        edit_menu.addAction(self.redo_action)

        self.reset_all_action = QAction(icon("refresh"), "전체 초기화", self)
        self.reset_all_action.triggered.connect(self._on_reset_all)
        edit_menu.addAction(self.reset_all_action)

        toolbar = QToolBar("주요 작업")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        toolbar.addWidget(self._build_brand_widget())
        toolbar.addSeparator()
        for action in (
            self.open_action,
            self.close_action,
            self.save_action,
            self.save_as_action,
            self.print_action,
            self.undo_action,
            self.redo_action,
            self.reset_all_action,
        ):
            toolbar.addAction(action)
        self.addToolBar(toolbar)

    def _build_brand_widget(self) -> QWidget:
        app_icon_path = Path(__file__).parent.parent / "resources" / "icons" / "app.ico"

        brand = QWidget()
        layout = QHBoxLayout(brand)
        layout.setContentsMargins(6, 0, 16, 0)
        layout.setSpacing(8)

        icon_label = QLabel()
        if app_icon_path.exists():
            icon_label.setPixmap(QPixmap(str(app_icon_path)).scaled(
                22, 22, Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
        layout.addWidget(icon_label)

        name_label = QLabel("Trans Pro")
        name_label.setStyleSheet("font-size: 15px; font-weight: 700; color: #ffffff;")
        layout.addWidget(name_label)

        return brand

    def _build_status_bar(self) -> None:
        self.status_progress = QProgressBar()
        self.status_progress.setRange(0, 0)
        self.status_progress.setMaximumWidth(160)
        self.status_progress.setVisible(False)
        self.statusBar().addPermanentWidget(self.status_progress)
        self.statusBar().showMessage("이미지를 열어주세요 (Ctrl+O)")

    # ------------------------------------------------------------------ 사이드바 / 도구 전환
    def _on_sidebar_row_changed(self, row: int) -> None:
        if row < 0:
            return
        kind = self._row_kind.get(row)
        if kind == "tool":
            self._last_tool_row = row
            self._activate_tool_panel(self._tool_rows[row])
        elif kind == "action":
            handler = self._action_handlers[row]
            handler()
            self.sidebar.blockSignals(True)
            self.sidebar.setCurrentRow(self._last_tool_row)
            self.sidebar.blockSignals(False)

    def _activate_tool_panel(self, index: int) -> None:
        if self._active_panel_index == PANEL_TEXT:
            self.canvas.clear_text_overlay()

        self._active_panel_index = index
        self.properties_panel.setCurrentIndex(index)
        self._refresh_canvas()

        if index == PANEL_ENHANCE:
            self._enhance_baseline = self.document.current
        elif index == PANEL_TEXT:
            self._text_baseline = self.document.current
            self.text_panel.emit_current_overlay()
        elif index == PANEL_QUALITY:
            self._quality_baseline = self.document.current

    def _select_tool_row(self, panel_index: int) -> None:
        row = next((r for r, idx in self._tool_rows.items() if idx == panel_index), None)
        if row is not None:
            self.sidebar.setCurrentRow(row)

    # ------------------------------------------------------------------ 파일 열기 / 닫기
    def _open_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "이미지 열기", "", _OPEN_FILTER)
        if not path:
            return
        self._open_path(path)

    def _open_path(self, path: str) -> None:
        try:
            image = open_image(path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "열기 실패", f"이미지를 열 수 없습니다:\n{exc}")
            return
        self.document.load(image)
        self._current_path = path
        self._remember_recent_file(path)
        self.center_stack.setCurrentIndex(STACK_EDITOR)
        self._activate_tool_panel(self._active_panel_index)
        self._update_actions_enabled()
        self.statusBar().showMessage(f"열림: {path} ({image.width}x{image.height})")

    def _on_home_quick_action(self, action: str) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "이미지 열기", "", _OPEN_FILTER)
        if not path:
            return
        self._open_path(path)
        target_panel = _QUICK_ACTION_PANEL.get(action)
        if target_panel is not None:
            self._select_tool_row(target_panel)

    def _on_close_image(self) -> None:
        if self.document.current is None:
            return
        if self.document.can_undo() or self.document.can_redo():
            reply = QMessageBox.question(
                self,
                "닫기",
                "저장하지 않은 변경 사항이 있을 수 있습니다. 그래도 닫을까요?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return
        self.document = ImageDocument()
        self._current_path = None
        self.canvas.set_image(None)
        self.center_stack.setCurrentIndex(STACK_HOME)
        self._update_actions_enabled()
        self.statusBar().showMessage("이미지를 열어주세요 (Ctrl+O)")

    # ------------------------------------------------------------------ 최근 작업 목록
    def _load_recent_files(self) -> None:
        recent = self._settings.value("recentFiles", [], type=list) or []
        self.home_widget.set_recent_files(recent)

    def _remember_recent_file(self, path: str) -> None:
        recent = self._settings.value("recentFiles", [], type=list) or []
        recent = [p for p in recent if p != path]
        recent.insert(0, path)
        recent = recent[:_MAX_RECENT_FILES]
        self._settings.setValue("recentFiles", recent)
        self.home_widget.set_recent_files(recent)

    # ------------------------------------------------------------------ 미리보기 / 적용
    def _on_preview_requested(self, fn, kwargs: dict) -> None:
        if self.document.current is None:
            return
        try:
            preview = fn(self.document.current, **kwargs)
        except Exception:  # noqa: BLE001
            logger.debug("미리보기 계산 실패", exc_info=True)
            return
        self.canvas.set_image(preview)

    def _apply_source_image(self) -> Image.Image | None:
        """이 요청이 적용될 원본 이미지를 고른다.

        품질개선 패널은 슬라이더 값을 바꿔가며 결과를 비교하는 용도라, 매번
        document.current(직전 결과)에 누적 적용하면 두 번째부터는 이미 처리된
        이미지 위에 다시 처리하는 꼴이라 값을 바꿔도 차이가 거의 안 보여
        "고정된" 것처럼 보인다. 이 도구에 들어왔을 때의 baseline에서 매번 다시
        적용해야 슬라이더 값 변경이 항상 눈에 보이는 결과로 이어진다.
        """
        if self._active_panel_index == PANEL_QUALITY and self._quality_baseline is not None:
            return self._quality_baseline
        return self.document.current

    def _on_apply_requested(self, fn, kwargs: dict, is_async: bool) -> None:
        source = self._apply_source_image()
        if source is None:
            QMessageBox.information(self, "알림", "먼저 이미지를 열어주세요.")
            return

        if is_async:
            self._run_async(fn, kwargs, source)
            return

        try:
            result = fn(source, **kwargs)
            self.document.apply_result(result)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "처리 실패", str(exc))
            return
        self._refresh_canvas()
        self._update_actions_enabled()

    def _run_async(self, fn, kwargs: dict, source_image: Image.Image | None = None) -> None:
        image = source_image if source_image is not None else self.document.current
        label = _ASYNC_BUSY_LABELS.get(getattr(fn, "__name__", ""), "처리 중...")
        self._set_busy(True, label)

        worker = ProcessWorker(fn, image=image, **kwargs)
        self._worker = worker  # GC 방지를 위해 참조 유지

        def on_ok(result: Image.Image) -> None:
            self._set_busy(False)
            try:
                self.document.apply_result(result)
            except Exception as exc:  # noqa: BLE001
                QMessageBox.critical(self, "처리 실패", str(exc))
                return
            self._refresh_canvas()
            self._update_actions_enabled()

        def on_fail(message: str) -> None:
            self._set_busy(False)
            QMessageBox.critical(self, "처리 실패", message)

        worker.finished_ok.connect(on_ok)
        worker.failed.connect(on_fail)
        worker.start()

    def _set_busy(self, busy: bool, message: str = "처리 중...") -> None:
        self.sidebar.setEnabled(not busy)
        self.properties_panel.setEnabled(not busy)
        self.status_progress.setVisible(busy)
        self.statusBar().showMessage(message if busy else "완료")
        self.canvas.set_busy(busy, message)

    # ------------------------------------------------------------------ 보정 초기화 (baseline 복귀)
    def _on_enhance_reset(self) -> None:
        if self._enhance_baseline is None or self.document.current is None:
            return
        if self.document.current is self._enhance_baseline:
            return
        self.document.apply_result(self._enhance_baseline)
        self._refresh_canvas()
        self._update_actions_enabled()

    # ------------------------------------------------------------------ 텍스트 드래그 오버레이
    def _resolve_text_pixel_size(self, size_percent: float) -> int:
        """이미지 높이 대비 퍼센트를 실제 픽셀 크기로 환산한다.

        고정 픽셀 크기를 쓰면 전체초기화 등으로 이미지 해상도가 달라졌을 때 같은
        값이라도 화면 비율이 달라 보여 "크기가 작아졌다"는 혼란을 준다. 항상 현재
        이미지 높이 기준으로 다시 계산하면 해상도가 바뀌어도 항상 같은 비율로 보인다.
        """
        height = self.document.current.height if self.document.current is not None else _DEFAULT_TEXT_HEIGHT_HINT
        return max(6, round(height * size_percent / 100))

    def _on_text_overlay_changed(self, params: dict) -> None:
        if self.document.current is None:
            return
        self.canvas.show_text_overlay(
            text=params.get("text", ""),
            size=self._resolve_text_pixel_size(params.get("size_percent", 6)),
            color=params.get("color", (255, 255, 255, 255)),
            rotation=params.get("rotation", 0.0),
            font_path=params.get("font_path"),
            shadow=params.get("shadow", True),
        )

    def _on_text_apply(self, params: dict) -> None:
        text = (params.get("text") or "").strip()
        if not text:
            QMessageBox.information(self, "텍스트 추가", "텍스트를 입력해주세요.")
            return
        if self.document.current is None:
            QMessageBox.information(self, "알림", "먼저 이미지를 열어주세요.")
            return
        position = self.canvas.get_text_overlay_position()
        kwargs = {
            "text": text,
            "position": position,
            "size": self._resolve_text_pixel_size(params.get("size_percent", 6)),
            "color": params.get("color", (255, 255, 255, 255)),
            "rotation": params.get("rotation", 0.0),
            "shadow": params.get("shadow", True),
            "font_path": params.get("font_path"),
        }
        try:
            self.document.apply(add_text, **kwargs)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "처리 실패", str(exc))
            return
        self.canvas.clear_text_overlay()
        self._refresh_canvas()
        self._update_actions_enabled()
        self.statusBar().showMessage("텍스트가 추가되었습니다.")

    def _on_text_reset(self) -> None:
        self.canvas.clear_text_overlay()
        if (
            self._text_baseline is not None
            and self.document.current is not None
            and self.document.current is not self._text_baseline
        ):
            self.document.apply_result(self._text_baseline)
            self._refresh_canvas()
            self._update_actions_enabled()
        self.statusBar().showMessage("텍스트 도구가 초기화되었습니다.")

    # ------------------------------------------------------------------ Undo/Redo/전체 초기화
    def _on_undo(self) -> None:
        self.document.undo()
        self._resync_active_panel()
        self._update_actions_enabled()

    def _on_redo(self) -> None:
        self.document.redo()
        self._resync_active_panel()
        self._update_actions_enabled()

    def _on_reset_all(self) -> None:
        if self.document.original is None or self.document.current is None:
            return
        if self.document.current is self.document.original:
            return
        reply = QMessageBox.question(
            self,
            "전체 초기화",
            "모든 편집 내용을 취소하고 원본 이미지로 되돌릴까요?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        self.document.apply_result(self.document.original)
        self._resync_active_panel()
        self._update_actions_enabled()

    def _resync_active_panel(self) -> None:
        """Undo/Redo/전체초기화처럼 document.current가 바깥에서 바뀌었을 때, 캔버스가
        들고 있던 도구별 상태(텍스트 오버레이 등)를 새 이미지 기준으로 다시 맞춘다."""
        self._activate_tool_panel(self._active_panel_index)

    def _update_actions_enabled(self) -> None:
        has_image = self.document.current is not None
        self.close_action.setEnabled(has_image)
        self.save_action.setEnabled(has_image)
        self.save_as_action.setEnabled(has_image)
        self.print_action.setEnabled(has_image)
        self.undo_action.setEnabled(self.document.can_undo())
        self.redo_action.setEnabled(self.document.can_redo())
        self.reset_all_action.setEnabled(has_image and self.document.current is not self.document.original)

    # ------------------------------------------------------------------ 저장 / 프린트
    def _on_quick_save(self) -> None:
        if self.document.current is None:
            QMessageBox.information(self, "저장", "저장할 이미지가 없습니다.")
            return
        parent_dir = os.path.dirname(self._current_path) if self._current_path else ""
        if not self._current_path or (parent_dir and not os.path.isdir(parent_dir)):
            # 원본 폴더가 더 이상 존재하지 않으면(외장 드라이브 분리 등) 조용히 실패시키는 대신
            # 다른 이름으로 저장 다이얼로그로 안내한다.
            self._on_save_as()
            return
        try:
            save_image(self.document.current, self._current_path, quality=_DEFAULT_SAVE_QUALITY)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "저장 실패", f"이미지를 저장할 수 없습니다:\n{exc}")
            return
        self.statusBar().showMessage(f"저장됨: {self._current_path}")

    def _save_dialog_start_path(self) -> str:
        """다이얼로그 시작 위치로 쓸 안전한 경로를 계산한다.

        _current_path가 가리키는 폴더가 (외장 드라이브 분리, 임시폴더 정리 등으로) 더
        이상 존재하지 않으면 그 경로를 그대로 네이티브 저장 다이얼로그에 넘겼을 때
        "파일이 없습니다. 파일 이름을 확인하고 다시 시도하십시오" 같은 오류가 날 수
        있다. 폴더가 실존할 때만 힌트로 사용하고, 아니면 빈 문자열로 OS 기본 위치를
        쓰게 한다.
        """
        if not self._current_path:
            return ""
        parent = os.path.dirname(self._current_path)
        if parent and not os.path.isdir(parent):
            return os.path.basename(self._current_path)
        return self._current_path

    def _on_save_as(self) -> None:
        if self.document.current is None:
            QMessageBox.information(self, "저장", "저장할 이미지가 없습니다.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "다른 이름으로 저장", self._save_dialog_start_path(), _SAVE_FILTER
        )
        if not path:
            return
        try:
            save_image(self.document.current, path, quality=_DEFAULT_SAVE_QUALITY)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "저장 실패", f"이미지를 저장할 수 없습니다:\n{exc}")
            return
        self._current_path = path
        self._remember_recent_file(path)
        self.statusBar().showMessage(f"저장됨: {path}")

    def _on_print(self) -> None:
        if self.document.current is None:
            QMessageBox.information(self, "인쇄", "출력할 이미지가 없습니다.")
            return

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        image = self.document.current.convert("RGB")
        qimage = ImageQt(image)
        pixmap = QPixmap.fromImage(qimage)

        painter = QPainter(printer)
        try:
            page_rect = printer.pageRect(QPrinter.Unit.DevicePixel)
            draw_w, draw_h = fit_to_page(
                (pixmap.width(), pixmap.height()),
                (int(page_rect.width()), int(page_rect.height())),
            )
            painter.drawPixmap(0, 0, draw_w, draw_h, pixmap)
        finally:
            painter.end()

    # ------------------------------------------------------------------ 캔버스 갱신
    def _refresh_canvas(self) -> None:
        self.canvas.set_image(self.document.current)


__all__ = ["MainWindow", "TOOL_PANEL_LABELS", "SUPPORTED_EXTENSIONS"]
