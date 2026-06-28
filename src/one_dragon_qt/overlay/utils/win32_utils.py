"""兼容层：保留旧 win32_utils 名称以避免破坏 import，委托到 platform.hotkey / platform.overlay。"""

from __future__ import annotations

import sys

from one_dragon.platform import get_platform_context

_user32 = None
_shcore = None

if sys.platform == 'win32':
    try:
        import ctypes
        _user32 = ctypes.windll.user32
    except (AttributeError, OSError):
        _user32 = None

VK_CONTROL = 0x11
VK_LCONTROL = 0xA2
VK_RCONTROL = 0xA3
VK_MENU = 0x12
VK_LMENU = 0xA4
VK_RMENU = 0xA5

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WDA_NONE = 0x0
WDA_EXCLUDEFROMCAPTURE = 0x11


def get_windows_build() -> int:
    return 0


def is_windows_build_supported(min_build: int = 19041) -> bool:
    return True


def get_process_dpi_awareness() -> int:
    return 0


def is_process_dpi_aware() -> bool:
    return False


def is_key_pressed(vk: int) -> bool:
    return get_platform_context().hotkey.is_key_pressed(int(vk))


def is_ctrl_pressed() -> bool:
    return get_platform_context().hotkey.is_ctrl_pressed()


def is_alt_pressed() -> bool:
    return get_platform_context().hotkey.is_alt_pressed()


def key_to_vk(key: str) -> int | None:
    return get_platform_context().hotkey.key_name_to_vk(key)


def is_hotkey_combo_pressed(main_key: str) -> bool:
    return get_platform_context().hotkey.is_hotkey_combo_pressed(main_key)


def is_window_minimized(hwnd: int | None) -> bool:
    return get_platform_context().hotkey.is_window_minimized(hwnd)


def is_window_visible(hwnd: int | None) -> bool:
    return get_platform_context().hotkey.is_window_visible(hwnd)


def set_window_click_through(hwnd: int | None, click_through: bool) -> bool:
    if hwnd is None:
        return False
    return get_platform_context().overlay.set_click_through(int(hwnd), bool(click_through))


def set_window_display_affinity(hwnd: int | None, exclude_from_capture: bool) -> bool:
    if hwnd is None:
        return False
    return get_platform_context().overlay.set_exclude_from_capture(int(hwnd), bool(exclude_from_capture))
