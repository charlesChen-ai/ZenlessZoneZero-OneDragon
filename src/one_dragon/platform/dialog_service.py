"""对话框 / 错误弹窗服务抽象。"""

from __future__ import annotations

from abc import ABC, abstractmethod


class DialogService(ABC):
    """模态错误/告警对话框。"""

    @abstractmethod
    def show_error(self, title: str, message: str) -> None:
        """显示错误弹窗，阻塞直到用户关闭。"""

    @abstractmethod
    def show_warning(self, title: str, message: str) -> None:
        """显示告警弹窗。"""

    @abstractmethod
    def show_info(self, title: str, message: str) -> None:
        """显示信息弹窗。"""

    @abstractmethod
    def confirm(self, title: str, message: str) -> bool:
        """确认对话框，返回 True 表示用户选了确定/是。"""
