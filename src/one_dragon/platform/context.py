"""平台检测与工厂。"""

from __future__ import annotations

import sys
from functools import lru_cache

from one_dragon.platform.clipboard_service import ClipboardService
from one_dragon.platform.console_service import ConsoleService
from one_dragon.platform.dialog_service import DialogService
from one_dragon.platform.hotkey_service import HotkeyService
from one_dragon.platform.input_service import InputService
from one_dragon.platform.overlay_service import OverlayService
from one_dragon.platform.screenshot_service import ScreenshotService
from one_dragon.platform.window_service import WindowService


def is_windows() -> bool:
    return sys.platform == 'win32'


def is_macos() -> bool:
    return sys.platform == 'darwin'


class PlatformContext:

    def __init__(
            self,
            window: WindowService,
            input: InputService,
            screenshot: ScreenshotService,
            clipboard: ClipboardService,
            overlay: OverlayService,
            hotkey: HotkeyService,
            dialog: DialogService,
            console: ConsoleService,
    ) -> None:
        self.window: WindowService = window
        self.input: InputService = input
        self.screenshot: ScreenshotService = screenshot
        self.clipboard: ClipboardService = clipboard
        self.overlay: OverlayService = overlay
        self.hotkey: HotkeyService = hotkey
        self.dialog: DialogService = dialog
        self.console: ConsoleService = console

    @property
    def name(self) -> str:
        return sys.platform


@lru_cache(maxsize=1)
def get_platform_context() -> PlatformContext:
    """获取当前平台的 :class:`PlatformContext`。"""
    if is_windows():
        from one_dragon.platform._impl.windows.context import build_windows_context
        return build_windows_context()
    if is_macos():
        from one_dragon.platform._impl.macos.context import build_macos_context
        return build_macos_context()
    # 其他平台暂用 Windows 的纯 pyautogui 兜底子集（截图/输入/剪贴板）。
    from one_dragon.platform._impl.fallback import build_fallback_context
    return build_fallback_context()
