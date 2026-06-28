"""macOS 平台 context 工厂。"""

from __future__ import annotations

from one_dragon.platform._impl.macos.clipboard_service import MacosClipboardService
from one_dragon.platform._impl.macos.console_service import MacosConsoleService
from one_dragon.platform._impl.macos.dialog_service import MacosDialogService
from one_dragon.platform._impl.macos.hotkey_service import MacosHotkeyService
from one_dragon.platform._impl.macos.input_service import MacosInputService
from one_dragon.platform._impl.macos.overlay_service import MacosOverlayService
from one_dragon.platform._impl.macos.screenshot_service import (
    MacosMssScreenshotService,
    MacosPilScreenshotService,
    MacosQuartzScreenshotService,
)
from one_dragon.platform._impl.macos.window_service import MacosWindowService
from one_dragon.platform.context import PlatformContext
from one_dragon.platform.screenshot_service import CompositeScreenshotService


def build_macos_context() -> PlatformContext:
    return PlatformContext(
        window=MacosWindowService(),
        input=MacosInputService(),
        screenshot=CompositeScreenshotService([
            MacosQuartzScreenshotService(),
            MacosMssScreenshotService(),
            MacosPilScreenshotService(),
        ]),
        clipboard=MacosClipboardService(),
        overlay=MacosOverlayService(),
        hotkey=MacosHotkeyService(),
        dialog=MacosDialogService(),
        console=MacosConsoleService(),
    )
