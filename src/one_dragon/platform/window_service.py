"""窗口服务抽象。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from one_dragon.base.geometry.rectangle import Rect


@dataclass
class WindowInfo:
    """平台无关的窗口描述。"""

    handle: int  # 平台原生句柄（HWND / CGWindowID）
    title: str
    pid: int
    bounds: Rect  # 整个窗口在屏幕上的矩形（含标题栏）


class WindowService(ABC):
    """窗口服务：负责找窗口、获取坐标、判断状态、激活。"""

    @abstractmethod
    def list_windows(self) -> list[WindowInfo]:
        """列出当前桌面所有可见窗口。"""

    @abstractmethod
    def find_by_title(self, title: str) -> WindowInfo | None:
        """按窗口标题精确匹配查找。"""

    @abstractmethod
    def find_by_title_contains(self, substring: str) -> list[WindowInfo]:
        """按窗口标题子串匹配查找。"""

    @abstractmethod
    def get_window_bounds(self, info: WindowInfo) -> Rect | None:
        """获取窗口在屏幕上的矩形（含标题栏）。"""

    @abstractmethod
    def get_client_rect(self, info: WindowInfo) -> Rect | None:
        """获取客户区在屏幕上的矩形（不含标题栏）。

        macOS 上 Quarz 返回的 Bounds 已不含标题栏，Windows 上需要先取 ClientRect 再 ClientToScreen。
        """

    @abstractmethod
    def client_to_screen(self, info: WindowInfo, x: int, y: int) -> tuple[int, int] | None:
        """把客户区坐标转换为屏幕坐标。"""

    @abstractmethod
    def screen_to_client(self, info: WindowInfo, x: int, y: int) -> tuple[int, int] | None:
        """把屏幕坐标转换为客户区坐标。"""

    @abstractmethod
    def is_window_valid(self, info: WindowInfo) -> bool:
        """窗口句柄是否仍然有效。"""

    @abstractmethod
    def is_minimized(self, info: WindowInfo) -> bool:
        """窗口是否最小化。"""

    @abstractmethod
    def is_visible(self, info: WindowInfo) -> bool:
        """窗口是否可见。"""

    @abstractmethod
    def restore(self, info: WindowInfo) -> bool:
        """如果最小化则恢复显示。"""

    @abstractmethod
    def activate(self, info: WindowInfo) -> bool:
        """将窗口激活到前台。"""

    @abstractmethod
    def get_foreground(self) -> WindowInfo | None:
        """获取当前前台窗口。"""

    @abstractmethod
    def set_foreground(self, info: WindowInfo) -> bool:
        """把指定窗口置为前台（不改变 z-order 时尽量用 send_to_back 等替代）。"""
