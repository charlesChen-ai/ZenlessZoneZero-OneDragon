"""Windows 平台 context 工厂。"""

from __future__ import annotations

from one_dragon.platform._impl.windows.clipboard_service import WindowsClipboardService
from one_dragon.platform._impl.windows.console_service import WindowsConsoleService
from one_dragon.platform._impl.windows.dialog_service import WindowsDialogService
from one_dragon.platform._impl.windows.hotkey_service import WindowsHotkeyService
from one_dragon.platform._impl.windows.input_service import WindowsInputService
from one_dragon.platform._impl.windows.overlay_service import WindowsOverlayService
from one_dragon.platform._impl.windows.screenshot_service import (
    WindowsBitBltScreenshotService,
    WindowsMssScreenshotService,
    WindowsPilScreenshotService,
    WindowsPrintWindowScreenshotService,
)
from one_dragon.platform._impl.windows.window_service import WindowsWindowService
from one_dragon.platform.context import PlatformContext
from one_dragon.platform.screenshot_service import CompositeScreenshotService


def build_windows_context() -> PlatformContext:
    return PlatformContext(
        window=WindowsWindowService(),
        input=WindowsInputService(),
        screenshot=CompositeScreenshotService([
            WindowsPrintWindowScreenshotService(),
            WindowsBitBltScreenshotService(),
            WindowsMssScreenshotService(),
            WindowsPilScreenshotService(),
        ]),
        clipboard=WindowsClipboardService(),
        overlay=WindowsOverlayService(),
        hotkey=WindowsHotkeyService(),
        dialog=WindowsDialogService(),
        console=WindowsConsoleService(),
    )
