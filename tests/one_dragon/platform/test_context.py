"""平台 context 工厂测试。"""

from __future__ import annotations

import sys

import pytest

pytest.importorskip("cv2")

from one_dragon.platform.context import (
    PlatformContext,
    get_platform_context,
    is_macos,
    is_windows,
)


def test_is_windows_matches_sys_platform() -> None:
    assert isinstance(is_windows(), bool)
    assert is_windows() == (sys.platform == "win32")


def test_is_macos_matches_sys_platform() -> None:
    assert isinstance(is_macos(), bool)
    assert is_macos() == (sys.platform == "darwin")


def test_is_windows_and_is_macos_are_mutually_exclusive() -> None:
    assert not (is_windows() and is_macos())


def test_get_platform_context_returns_platform_context() -> None:
    ctx = get_platform_context()
    assert ctx is not None
    assert isinstance(ctx, PlatformContext)
    assert ctx.name == sys.platform


def test_platform_context_has_all_required_services() -> None:
    from one_dragon.platform.clipboard_service import ClipboardService
    from one_dragon.platform.console_service import ConsoleService
    from one_dragon.platform.dialog_service import DialogService
    from one_dragon.platform.hotkey_service import HotkeyService
    from one_dragon.platform.input_service import InputService
    from one_dragon.platform.overlay_service import OverlayService
    from one_dragon.platform.window_service import WindowService

    ctx = get_platform_context()
    assert isinstance(ctx.window, WindowService)
    assert isinstance(ctx.input, InputService)
    assert ctx.screenshot is not None
    assert isinstance(ctx.clipboard, ClipboardService)
    assert isinstance(ctx.overlay, OverlayService)
    assert isinstance(ctx.hotkey, HotkeyService)
    assert isinstance(ctx.dialog, DialogService)
    assert isinstance(ctx.console, ConsoleService)


def test_platform_context_is_singleton() -> None:
    assert get_platform_context() is get_platform_context()
