"""跨平台最低实现兜底。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from one_dragon.platform.console_service import ConsoleService
from one_dragon.platform.screenshot_service import (
    CompositeScreenshotService,
)

if TYPE_CHECKING:
    from one_dragon.platform.context import PlatformContext


class NoopConsoleService(ConsoleService):

    def hide_console(self) -> None:
        return None

    def run_with_cleanup(self, fn) -> None:
        fn()


def build_fallback_context() -> PlatformContext:
    """未知平台时使用 pyautogui / pynput 的最简兜底（仅截图 + 输入 + 剪贴板）。"""
    from one_dragon.platform._impl.fallback_impl import (
        FallbackClipboardService,
        FallbackInputService,
        FallbackScreenshotService,
        FallbackWindowService,
        NoopDialogService,
        NoopHotkeyService,
        NoopOverlayService,
    )
    from one_dragon.platform.context import PlatformContext

    return PlatformContext(
        window=FallbackWindowService(),
        input=FallbackInputService(),
        screenshot=CompositeScreenshotService([FallbackScreenshotService()]),
        clipboard=FallbackClipboardService(),
        overlay=NoopOverlayService(),
        hotkey=NoopHotkeyService(),
        dialog=NoopDialogService(),
        console=NoopConsoleService(),
    )


__all__ = ['build_fallback_context']
