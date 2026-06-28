"""Windows 平台窗口服务。"""

from __future__ import annotations

import ctypes
from ctypes import wintypes

from one_dragon.base.geometry.rectangle import Rect
from one_dragon.platform.window_service import WindowInfo, WindowService
from one_dragon.utils.log_utils import log

_user32 = ctypes.windll.user32
_user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
_user32.GetWindowThreadProcessId.restype = wintypes.DWORD
_user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
_user32.GetWindowRect.restype = wintypes.BOOL
_user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
_user32.GetClientRect.restype = wintypes.BOOL
_user32.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINT]
_user32.ClientToScreen.restype = wintypes.BOOL
_user32.ScreenToClient.argtypes = [wintypes.HWND, ctypes.POINT]
_user32.ScreenToClient.restype = wintypes.BOOL
_user32.IsWindow.argtypes = [wintypes.HWND]
_user32.IsWindow.restype = wintypes.BOOL
_user32.IsIconic.argtypes = [wintypes.HWND]
_user32.IsIconic.restype = wintypes.BOOL
_user32.IsWindowVisible.argtypes = [wintypes.HWND]
_user32.IsWindowVisible.restype = wintypes.BOOL
_user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
_user32.ShowWindow.restype = wintypes.BOOL
_user32.SetForegroundWindow.argtypes = [wintypes.HWND]
_user32.SetForegroundWindow.restype = wintypes.BOOL
_user32.GetForegroundWindow.argtypes = []
_user32.GetForegroundWindow.restype = wintypes.HWND
_user32.GetWindowTextW.argtypes = [wintypes.HWND, ctypes.c_wchar_p, ctypes.c_int]
_user32.GetWindowTextW.restype = ctypes.c_int
_user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
_user32.GetWindowTextLengthW.restype = ctypes.c_int
_user32.EnumWindows.argtypes = [ctypes.c_void_p, wintypes.LPARAM]
_user32.EnumWindows.restype = wintypes.BOOL
_user32.GetClassNameW.argtypes = [wintypes.HWND, ctypes.c_wchar_p, ctypes.c_int]
_user32.GetClassNameW.restype = ctypes.c_int

EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

GA_ROOT = 2
GA_ROOTOWNER = 3


def _get_window_title(hwnd: int) -> str:
    length = _user32.GetWindowTextLengthW(hwnd)
    if length <= 0:
        return ''
    buf = ctypes.create_unicode_buffer(length + 1)
    _user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value or ''


def _get_window_pid(hwnd: int) -> int:
    pid = wintypes.DWORD()
    _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return int(pid.value)


def _get_window_rect(hwnd: int) -> Rect | None:
    rect = wintypes.RECT()
    if not _user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return None
    return Rect(int(rect.left), int(rect.top), int(rect.right), int(rect.bottom))


def _get_client_rect_on_screen(hwnd: int) -> Rect | None:
    crect = wintypes.RECT()
    if not _user32.GetClientRect(hwnd, ctypes.byref(crect)):
        return None
    left_top = wintypes.POINT(crect.left, crect.top)
    if not _user32.ClientToScreen(hwnd, ctypes.byref(left_top)):
        return None
    right_bottom = wintypes.POINT(crect.right, crect.bottom)
    if not _user32.ClientToScreen(hwnd, ctypes.byref(right_bottom)):
        return None
    return Rect(int(left_top.x), int(left_top.y), int(right_bottom.x), int(right_bottom.y))


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


def _make_window_info(hwnd: int) -> WindowInfo | None:
    if not hwnd:
        return None
    bounds = _get_window_rect(int(hwnd))
    if bounds is None:
        return None
    return WindowInfo(
        handle=int(hwnd),
        title=_get_window_title(int(hwnd)),
        pid=_get_window_pid(int(hwnd)),
        bounds=bounds,
    )


class WindowsWindowService(WindowService):

    def list_windows(self) -> list[WindowInfo]:
        result: list[WindowInfo] = []

        def cb(hwnd, _lparam):
            if not _user32.IsWindowVisible(hwnd):
                return True
            info = _make_window_info(int(hwnd))
            if info is not None and info.title:
                result.append(info)
            return True

        _user32.EnumWindows(EnumWindowsProc(cb), 0)
        return result

    def find_by_title(self, title: str) -> WindowInfo | None:
        for info in self.list_windows():
            if info.title == title:
                return info
        return None

    def find_by_title_contains(self, substring: str) -> list[WindowInfo]:
        return [w for w in self.list_windows() if substring in w.title]

    def get_window_bounds(self, info: WindowInfo) -> Rect | None:
        return _get_window_rect(int(info.handle))

    def get_client_rect(self, info: WindowInfo) -> Rect | None:
        return _get_client_rect_on_screen(int(info.handle))

    def client_to_screen(self, info: WindowInfo, x: int, y: int) -> tuple[int, int] | None:
        pt = wintypes.POINT(int(x), int(y))
        if not _user32.ClientToScreen(int(info.handle), ctypes.byref(pt)):
            return None
        return int(pt.x), int(pt.y)

    def screen_to_client(self, info: WindowInfo, x: int, y: int) -> tuple[int, int] | None:
        pt = wintypes.POINT(int(x), int(y))
        if not _user32.ScreenToClient(int(info.handle), ctypes.byref(pt)):
            return None
        return int(pt.x), int(pt.y)

    def is_window_valid(self, info: WindowInfo) -> bool:
        return bool(_user32.IsWindow(int(info.handle)))

    def is_minimized(self, info: WindowInfo) -> bool:
        return bool(_user32.IsIconic(_root_hwnd(int(info.handle))))

    def is_visible(self, info: WindowInfo) -> bool:
        return bool(_user32.IsWindowVisible(_root_hwnd(int(info.handle))))

    def restore(self, info: WindowInfo) -> bool:
        hwnd = int(info.handle)
        if not self.is_minimized(info):
            return True
        # SW_SHOWNOACTIVATE
        return bool(_user32.ShowWindow(hwnd, 4))

    def activate(self, info: WindowInfo) -> bool:
        try:
            return bool(_user32.SetForegroundWindow(int(info.handle)))
        except Exception as e:
            log.warning('激活窗口失败: %s', e)
            return False

    def get_foreground(self) -> WindowInfo | None:
        hwnd = _user32.GetForegroundWindow()
        if not hwnd:
            return None
        return _make_window_info(int(hwnd))

    def set_foreground(self, info: WindowInfo) -> bool:
        return self.activate(info)
