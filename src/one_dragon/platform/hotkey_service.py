"""热键 / 全局键盘状态服务抽象。"""

from __future__ import annotations

from abc import ABC, abstractmethod


class HotkeyService(ABC):
    """全局键盘状态查询。

    用于 Overlay 检测 ``Ctrl+Alt+某键`` 这种全局热键，以及 Ctrl / Alt 单键状态。
    """

    @abstractmethod
    def is_key_pressed(self, vk: int) -> bool:
        """指定虚拟键是否处于按下状态。"""

    @abstractmethod
    def is_ctrl_pressed(self) -> bool:
        """Ctrl / 左 Ctrl / 右 Ctrl 任一被按下。"""

    @abstractmethod
    def is_alt_pressed(self) -> bool:
        """Alt / 左 Alt / 右 Alt 任一被按下。"""

    @abstractmethod
    def key_name_to_vk(self, key: str) -> int | None:
        """把可读键名（如 ``f1``、``a``、``space``）转换为虚拟键码，找不到返回 None。"""

    @abstractmethod
    def is_hotkey_combo_pressed(self, main_key: str) -> bool:
        """Ctrl+Alt+main_key 是否同时被按下。"""

    @abstractmethod
    def is_window_minimized(self, hwnd: int | None) -> bool:
        """窗口是否最小化（hwnd 为 None 返回 False）。"""

    @abstractmethod
    def is_window_visible(self, hwnd: int | None) -> bool:
        """窗口是否可见。"""
