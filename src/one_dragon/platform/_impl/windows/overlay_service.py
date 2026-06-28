"""Windows 平台 Overlay：WS_EX_TRANSPARENT + WDA_EXCLUDEFROMCAPTURE。"""

from __future__ import annotations

import ctypes
from ctypes import wintypes

from one_dragon.platform.overlay_service import OverlayService

_user32 = ctypes.windll.user32
_user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
_user32.GetWindowLongW.restype = ctypes.c_long
_user32.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_long]
_user32.SetWindowLongW.restype = ctypes.c_long
_user32.SetWindowDisplayAffinity.argtypes = [wintypes.HWND, wintypes.DWORD]
_user32.SetWindowDisplayAffinity.restype = wintypes.BOOL

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WDA_NONE = 0x0
WDA_EXCLUDEFROMCAPTURE = 0x11


class WindowsOverlayService(OverlayService):

    def set_click_through(self, hwnd: int, enabled: bool) -> bool:
        if not hwnd:
            return False
        try:
            ctypes.set_last_error(0)
            old_style = _user32.GetWindowLongW(int(hwnd), GWL_EXSTYLE)
            if old_style == 0 and ctypes.get_last_error() != 0:
                return False
            new_style = old_style | WS_EX_LAYERED
            if enabled:
                new_style |= WS_EX_TRANSPARENT
            else:
                new_style &= ~WS_EX_TRANSPARENT
            ctypes.set_last_error(0)
            result = _user32.SetWindowLongW(int(hwnd), GWL_EXSTYLE, new_style)
            return not (result == 0 and ctypes.get_last_error() != 0)
        except Exception:
            return False

    def set_exclude_from_capture(self, hwnd: int, enabled: bool) -> bool:
        if not hwnd:
            return False
        affinity = WDA_EXCLUDEFROMCAPTURE if enabled else WDA_NONE
        return bool(_user32.SetWindowDisplayAffinity(int(hwnd), affinity))
