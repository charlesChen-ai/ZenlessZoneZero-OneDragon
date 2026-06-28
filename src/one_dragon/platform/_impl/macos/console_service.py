"""macOS 平台控制台：hide_console 为 noop；run_with_cleanup 用 atexit + psutil。"""

from __future__ import annotations

import atexit
import contextlib
import os
import signal
from collections.abc import Callable

from one_dragon.platform.console_service import ConsoleService
from one_dragon.utils.log_utils import log


class MacosConsoleService(ConsoleService):

    def hide_console(self) -> None:
        # macOS 启动 GUI .app 时本就没有控制台，no-op
        return None

    def run_with_cleanup(self, fn: Callable[[], None]) -> None:
        # macOS 上没有 JobObject；用 atexit + 进程组清理
        try:
            import psutil
            current = psutil.Process(os.getpid())
        except ImportError:
            log.debug('psutil 未安装，子进程清理退化为 atexit')
            atexit.register(lambda: None)
            return fn()
        atexit.register(self._kill_children, current)
        return fn()

    @staticmethod
    def _kill_children(parent) -> None:
        with contextlib.suppress(Exception):
            for child in parent.children(recursive=True):
                with contextlib.suppress(Exception):
                    child.send_signal(signal.SIGTERM)
