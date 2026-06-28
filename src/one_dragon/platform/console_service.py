"""控制台 / 启动器辅助服务抽象。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable


class ConsoleService(ABC):
    """控制台窗口与进程组管理。"""

    @abstractmethod
    def hide_console(self) -> None:
        """隐藏当前控制台窗口（仅 Windows 有意义，其它平台 noop）。"""

    @abstractmethod
    def run_with_cleanup(self, fn: Callable[[], None]) -> None:
        """运行 ``fn``，并保证 fn 退出时子进程一起被回收。

        Windows 上用 JobObject 实现；macOS 上用 atexit + psutil / pgrep 兜底。
        """
