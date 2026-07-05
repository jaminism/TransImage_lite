from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from PIL import Image, ImageOps


@dataclass
class ImageDocument:
    """이미지 상태와 Undo/Redo 히스토리를 관리한다.

    실제 편집 알고리즘(리사이즈/보정/배경제거 등)은 core.processors 하위 모듈에서
    순수 함수로 구현되고, apply()를 통해 이 문서에 적용된다.
    """

    original: Optional[Image.Image] = None
    current: Optional[Image.Image] = None
    _undo_stack: List[Image.Image] = field(default_factory=list)
    _redo_stack: List[Image.Image] = field(default_factory=list)

    def load(self, image: Image.Image) -> None:
        image = ImageOps.exif_transpose(image) or image
        self.original = image
        self.current = image
        self._undo_stack.clear()
        self._redo_stack.clear()

    def apply(self, processor_fn: Callable[..., Image.Image], **params) -> None:
        if self.current is None:
            raise ValueError("적용할 이미지가 없습니다.")
        self._undo_stack.append(self.current)
        self._redo_stack.clear()
        self.current = processor_fn(self.current, **params)

    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    def can_redo(self) -> bool:
        return bool(self._redo_stack)

    def undo(self) -> None:
        if not self._undo_stack or self.current is None:
            return
        self._redo_stack.append(self.current)
        self.current = self._undo_stack.pop()

    def redo(self) -> None:
        if not self._redo_stack or self.current is None:
            return
        self._undo_stack.append(self.current)
        self.current = self._redo_stack.pop()
