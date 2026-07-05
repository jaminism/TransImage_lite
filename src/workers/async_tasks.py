from __future__ import annotations

from typing import Any, Callable

from PySide6.QtCore import QThread, Signal


class ProcessWorker(QThread):
    """무거운 이미지 처리 함수를 백그라운드 스레드에서 실행한다.

    UI 스레드를 블로킹하지 않기 위해 품질 개선/배경 제거처럼 수 초가 걸리는
    처리는 반드시 이 워커를 통해 호출한다.
    """

    finished_ok = Signal(object)
    failed = Signal(str)

    def __init__(self, fn: Callable[..., Any], **kwargs: Any) -> None:
        super().__init__()
        self._fn = fn
        self._kwargs = kwargs

    def run(self) -> None:
        try:
            result = self._fn(**self._kwargs)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))
            return
        self.finished_ok.emit(result)
