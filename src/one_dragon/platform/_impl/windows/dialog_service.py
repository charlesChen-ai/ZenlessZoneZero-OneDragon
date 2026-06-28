"""Windows 平台对话框：使用 ctypes 直接调 user32.MessageBoxW。"""

from __future__ import annotations

import ctypes
from ctypes import wintypes

from one_dragon.platform.dialog_service import DialogService

_user32 = ctypes.windll.user32
_user32.MessageBoxW.argtypes = [wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.UINT]
_user32.MessageBoxW.restype = ctypes.c_int

MB_OK = 0x0
MB_OKCANCEL = 0x1
MB_YESNO = 0x4
MB_ICONERROR = 0x10
MB_ICONWARNING = 0x30
MB_ICONINFORMATION = 0x40

IDOK = 1
IDCANCEL = 2
IDYES = 6
IDNO = 7


class WindowsDialogService(DialogService):

    def show_error(self, title: str, message: str) -> None:
        _user32.MessageBoxW(0, message, title, MB_OK | MB_ICONERROR)

    def show_warning(self, title: str, message: str) -> None:
        _user32.MessageBoxW(0, message, title, MB_OK | MB_ICONWARNING)

    def show_info(self, title: str, message: str) -> None:
        _user32.MessageBoxW(0, message, title, MB_OK | MB_ICONINFORMATION)

    def confirm(self, title: str, message: str) -> bool:
        # 保持与旧行为一致：MB_OKCANCEL + MB_ICONERROR -> IDOK
        result = _user32.MessageBoxW(0, message, title, MB_OKCANCEL | MB_ICONERROR)
        return result == IDOK
