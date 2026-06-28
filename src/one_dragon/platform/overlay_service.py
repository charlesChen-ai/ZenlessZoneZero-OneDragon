"""Overlay（浮窗）服务抽象。

负责设置 PySide6 浮层窗口的：
- 鼠标穿透（``WS_EX_TRANSPARENT`` / ``NSWindowIgnoresMouseEvents``）
- 截图排除（``WDA_EXCLUDEFROMCAPTURE``，macOS 无公开 API）
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class OverlayService(ABC):
    """Overlay 窗口行为。"""

    @abstractmethod
    def set_click_through(self, hwnd: int, enabled: bool) -> bool:
        """设置窗口是否鼠标穿透。"""

    @abstractmethod
    def set_exclude_from_capture(self, hwnd: int, enabled: bool) -> bool:
        """设置窗口是否对系统截图不可见。macOS 上通常为 noop。"""
