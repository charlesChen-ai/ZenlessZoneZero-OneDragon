"""截图服务抽象。"""

from __future__ import annotations

from abc import ABC, abstractmethod

from cv2.typing import MatLike

from one_dragon.base.geometry.rectangle import Rect


class ScreenshotService(ABC):
    """单种截图策略的抽象。"""

    @property
    @abstractmethod
    def method_name(self) -> str:
        """策略名，对应 ``ScreenshotMethodEnum.value.value``。"""

    @abstractmethod
    def is_available(self) -> bool:
        """当前平台/环境是否支持此策略。"""

    @abstractmethod
    def capture(self, rect: Rect) -> MatLike | None:
        """按 ``rect`` 截取屏幕区域，返回 RGB 数组（与现有 PIL/MSS 一致）。"""


class CompositeScreenshotService:
    """按优先级依次尝试多个截图策略，命中即返回。"""

    def __init__(self, services: list[ScreenshotService]) -> None:
        self._services: list[ScreenshotService] = services

    @property
    def available_methods(self) -> list[str]:
        return [s.method_name for s in self._services if s.is_available()]

    def capture(self, rect: Rect) -> MatLike | None:
        for svc in self._services:
            if not svc.is_available():
                continue
            try:
                img = svc.capture(rect)
            except Exception:
                continue
            if img is not None:
                return img
        return None
