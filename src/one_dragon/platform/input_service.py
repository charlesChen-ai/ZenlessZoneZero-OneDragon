"""输入服务抽象。"""

from __future__ import annotations

from abc import ABC, abstractmethod


class InputService(ABC):
    """键鼠输入服务。

    所有坐标都是**屏幕绝对坐标**（已考虑 DPI / 缩放），调用方负责把游戏内坐标换算到屏幕坐标。
    """

    @abstractmethod
    def click(self, x: int, y: int, button: str = 'left', press_time: float = 0) -> None:
        """在屏幕坐标 (x, y) 处点击。"""

    @abstractmethod
    def double_click(self, x: int, y: int, button: str = 'left') -> None:
        """双击。"""

    @abstractmethod
    def move_to(self, x: int, y: int) -> None:
        """把鼠标移动到屏幕坐标 (x, y)。"""

    @abstractmethod
    def move_relative(self, dx: int, dy: int) -> None:
        """相对当前鼠标位置移动 dx/dy 像素。"""

    @abstractmethod
    def drag(self, sx: int, sy: int, ex: int, ey: int, duration: float = 0.5) -> None:
        """从 (sx, sy) 拖动到 (ex, ey)，按左键不放。"""

    @abstractmethod
    def scroll(self, clicks: int, x: int | None = None, y: int | None = None) -> None:
        """滚动；clicks 负数表示向上。"""

    @abstractmethod
    def key_tap(self, key: str) -> None:
        """按下并释放一个键。"""

    @abstractmethod
    def key_press(self, key: str) -> None:
        """按下一个键不释放。"""

    @abstractmethod
    def key_release(self, key: str) -> None:
        """释放一个键。"""

    @abstractmethod
    def hotkey(self, *keys: str) -> None:
        """按下组合键（如 ``ctrl`` + ``v``）。"""

    @abstractmethod
    def type_text(self, text: str, interval: float = 0.1) -> None:
        """逐字输入文本。"""

    @abstractmethod
    def get_mouse_pos(self) -> tuple[int, int]:
        """获取当前鼠标屏幕坐标。"""

    @abstractmethod
    def get_mouse_sensitivity(self) -> int:
        """获取系统鼠标灵敏度。Windows 上读 SystemParametersInfo SPI_GETMOUSESPEED。"""
