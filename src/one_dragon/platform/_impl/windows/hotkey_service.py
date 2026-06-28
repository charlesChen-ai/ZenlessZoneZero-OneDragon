"""Windows 平台热键 / 窗口状态查询。"""

from __future__ import annotations

import ctypes
import re
from ctypes import wintypes

from one_dragon.platform.hotkey_service import HotkeyService

_user32 = ctypes.windll.user32
_user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
_user32.GetAsyncKeyState.restype = ctypes.c_short
_user32.IsIconic.argtypes = [wintypes.HWND]
_user32.IsIconic.restype = wintypes.BOOL
_user32.IsWindowVisible.argtypes = [wintypes.HWND]
_user32.IsWindowVisible.restype = wintypes.BOOL
_user32.GetAncestor.argtypes = [wintypes.HWND, ctypes.c_uint]
_user32.GetAncestor.restype = wintypes.HWND
_user32.GetWindowPlacement.argtypes = [wintypes.HWND, ctypes.POINTER(ctypes.c_byte * 64)]
_user32.GetWindowPlacement.restype = wintypes.BOOL

GA_ROOT = 2
GA_ROOTOWNER = 3

VK_CONTROL = 0x11
VK_LCONTROL = 0xA2
VK_RCONTROL = 0xA3
VK_MENU = 0x12
VK_LMENU = 0xA4
VK_RMENU = 0xA5

SW_SHOWMINIMIZED = 2
SW_MINIMIZE = 6
SW_SHOWMINNOACTIVE = 7


class WINDOWPLACEMENT(ctypes.Structure):
    _fields_ = [
        ('length', wintypes.UINT),
        ('flags', wintypes.UINT),
        ('showCmd', wintypes.UINT),
        ('ptMinPosition', wintypes.POINT),
        ('ptMaxPosition', wintypes.POINT),
        ('rcNormalPosition', wintypes.RECT),
    ]


_KEY_NAME_MAP = {
    'space': 0x20,
    'tab': 0x09,
    'enter': 0x0D,
    'esc': 0x1B,
    'escape': 0x1B,
    'backspace': 0x08,
    'delete': 0x2E,
    'insert': 0x2D,
    'home': 0x24,
    'end': 0x23,
    'page_up': 0x21,
    'page_down': 0x22,
    'up': 0x26,
    'down': 0x28,
    'left': 0x25,
    'right': 0x27,
    'minus': 0xBD,
    'equals': 0xBB,
    'comma': 0xBC,
    'period': 0xBE,
    'slash': 0xBF,
    'backslash': 0xDC,
    'semicolon': 0xBA,
    'apostrophe': 0xDE,
    'grave': 0xC0,
    'l_bracket': 0xDB,
    'r_bracket': 0xDD,
}


def _root_hwnd(hwnd: int) -> int:
    try:
        root_owner = int(_user32.GetAncestor(int(hwnd), GA_ROOTOWNER) or 0)
        if root_owner:
            return root_owner
        root = int(_user32.GetAncestor(int(hwnd), GA_ROOT) or 0)
        if root:
            return root
    except Exception:
        pass
    return int(hwnd)


class WindowsHotkeyService(HotkeyService):

    def is_key_pressed(self, vk: int) -> bool:
        state = _user32.GetAsyncKeyState(int(vk))
        return bool(state & 0x8000)

    def is_ctrl_pressed(self) -> bool:
        return self.is_key_pressed(VK_CONTROL) or self.is_key_pressed(VK_LCONTROL) or self.is_key_pressed(VK_RCONTROL)

    def is_alt_pressed(self) -> bool:
        return self.is_key_pressed(VK_MENU) or self.is_key_pressed(VK_LMENU) or self.is_key_pressed(VK_RMENU)

    def key_name_to_vk(self, key: str) -> int | None:
        name = str(key or '').strip().lower()
        if not name:
            return None
        vk_match = re.fullmatch(r'vk_(\d+)', name)
        if vk_match:
            vk = int(vk_match.group(1))
            if 0 <= vk <= 254:
                return vk
            return None
        if len(name) == 1 and name.isalnum():
            return ord(name.upper())
        if name.startswith('numpad_'):
            suffix = name.replace('numpad_', '', 1)
            if suffix.isdigit():
                num = int(suffix)
                if 0 <= num <= 9:
                    return 0x60 + num
        fn_match = re.fullmatch(r'f(\d{1,2})', name)
        if fn_match:
            fn_num = int(fn_match.group(1))
            if 1 <= fn_num <= 24:
                return 0x70 + fn_num - 1
        return _KEY_NAME_MAP.get(name)

    def is_hotkey_combo_pressed(self, main_key: str) -> bool:
        vk = self.key_name_to_vk(main_key)
        if vk is None:
            return False
        return self.is_ctrl_pressed() and self.is_alt_pressed() and self.is_key_pressed(vk)

    def is_window_minimized(self, hwnd: int | None) -> bool:
        if hwnd is None or int(hwnd) == 0:
            return False
        target = _root_hwnd(int(hwnd))
        if bool(_user32.IsIconic(target)):
            return True
        placement = WINDOWPLACEMENT()
        placement.length = ctypes.sizeof(WINDOWPLACEMENT)
        if not _user32.GetWindowPlacement(target, ctypes.byref(placement)):
            return False
        return placement.showCmd in (SW_SHOWMINIMIZED, SW_MINIMIZE, SW_SHOWMINNOACTIVE)

    def is_window_visible(self, hwnd: int | None) -> bool:
        if hwnd is None or int(hwnd) == 0:
            return False
        return bool(_user32.IsWindowVisible(_root_hwnd(int(hwnd))))
