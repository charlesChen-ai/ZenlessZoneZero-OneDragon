"""Windows 平台截图服务。"""

from __future__ import annotations

import ctypes
from ctypes import wintypes

import cv2
import numpy as np
from cv2.typing import MatLike
from mss.base import MSSBase

from one_dragon.base.geometry.rectangle import Rect
from one_dragon.platform.screenshot_service import ScreenshotService

_user32 = ctypes.windll.user32
_gdi32 = ctypes.windll.gdi32

PW_RENDERFULLCONTENT = 0x00000002


class WindowsMssScreenshotService(ScreenshotService):
    """使用 mss 抓桌面区域（跨平台，但这里仅 Windows 注册）。"""

    def __init__(self) -> None:
        self._mss: MSSBase | None = None

    @property
    def method_name(self) -> str:
        return 'mss'

    def is_available(self) -> bool:
        return True

    def _get_mss(self) -> MSSBase | None:
        if self._mss is None:
            try:
                from mss import mss
                self._mss = mss()
            except Exception:
                self._mss = None
        return self._mss

    def capture(self, rect: Rect) -> MatLike | None:
        mss_instance = self._get_mss()
        if mss_instance is None:
            return None
        monitor = {'top': int(rect.y1), 'left': int(rect.x1), 'width': int(rect.width), 'height': int(rect.height)}
        try:
            shot = mss_instance.grab(monitor)
            return cv2.cvtColor(np.array(shot), cv2.COLOR_BGRA2RGB)
        except Exception:
            return None


class WindowsPilScreenshotService(ScreenshotService):
    """使用 pyautogui（基于 PIL.ImageGrab）截图。"""

    @property
    def method_name(self) -> str:
        return 'pil'

    def is_available(self) -> bool:
        return True

    def capture(self, rect: Rect) -> MatLike | None:
        try:
            from pyautogui import screenshot as pg_screenshot
            img = pg_screenshot(region=(int(rect.x1), int(rect.y1), int(rect.width), int(rect.height)))
        except Exception:
            return None
        return np.array(img)


class WindowsPrintWindowScreenshotService(ScreenshotService):
    """使用 PrintWindow API 抓指定 hwnd 的画面。"""

    def __init__(self) -> None:
        self._mfc_dc: int | None = None
        self._save_bitmap: int | None = None

    @property
    def method_name(self) -> str:
        return 'print_window'

    def is_available(self) -> bool:
        return True

    def capture(self, rect: Rect) -> MatLike | None:
        try:
            hwnd = int(getattr(rect, 'hwnd', 0)) if hasattr(rect, 'hwnd') else 0
        except Exception:
            hwnd = 0
        if not hwnd:
            return None
        try:
            hwnd_dc = _user32.GetDC(hwnd)
            if not hwnd_dc:
                return None
            try:
                mfc_dc = _gdi32.CreateCompatibleDC(hwnd_dc)
                if not mfc_dc:
                    return None
                try:
                    w = int(rect.width)
                    h = int(rect.height)
                    bitmap_info = self._build_bitmap_info(w, h)
                    save_bitmap = _gdi32.CreateDIBSection(mfc_dc, ctypes.byref(bitmap_info), 0, None, 0, 0)
                    if not save_bitmap:
                        return None
                    try:
                        prev_obj = _gdi32.SelectObject(mfc_dc, save_bitmap)
                        try:
                            ok = _user32.PrintWindow(hwnd, mfc_dc, PW_RENDERFULLCONTENT)
                            if not ok:
                                return None
                            buf = self._extract_bitmap(mfc_dc, w, h)
                            return np.frombuffer(buf, dtype=np.uint8).reshape(h, w, 4)[:, :, :3].copy()
                        finally:
                            _gdi32.SelectObject(mfc_dc, prev_obj)
                    finally:
                        _gdi32.DeleteObject(save_bitmap)
                finally:
                    _gdi32.DeleteDC(mfc_dc)
            finally:
                _user32.ReleaseDC(hwnd, hwnd_dc)
        except Exception:
            return None

    @staticmethod
    def _build_bitmap_info(width: int, height: int):
        class BITMAPINFOHEADER(ctypes.Structure):
            _fields_ = [
                ('biSize', wintypes.DWORD),
                ('biWidth', ctypes.c_long),
                ('biHeight', ctypes.c_long),
                ('biPlanes', wintypes.WORD),
                ('biBitCount', wintypes.WORD),
                ('biCompression', wintypes.DWORD),
                ('biSizeImage', wintypes.DWORD),
                ('biXPelsPerMeter', ctypes.c_long),
                ('biYPelsPerMeter', ctypes.c_long),
                ('biClrUsed', wintypes.DWORD),
                ('biClrImportant', wintypes.DWORD),
            ]

        class BITMAPINFO(ctypes.Structure):
            _fields_ = [
                ('bmiHeader', BITMAPINFOHEADER),
                ('bmiColors', wintypes.DWORD * 3),
            ]

        info = BITMAPINFO()
        info.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        info.bmiHeader.biWidth = width
        info.bmiHeader.biHeight = -height  # top-down
        info.bmiHeader.biPlanes = 1
        info.bmiHeader.biBitCount = 32
        info.bmiHeader.biCompression = 0  # BI_RGB
        return info

    @staticmethod
    def _extract_bitmap(mfc_dc: int, width: int, height: int) -> bytes:
        class BITMAPINFOHEADER(ctypes.Structure):
            _fields_ = [
                ('biSize', wintypes.DWORD),
                ('biWidth', ctypes.c_long),
                ('biHeight', ctypes.c_long),
                ('biPlanes', wintypes.WORD),
                ('biBitCount', wintypes.WORD),
                ('biCompression', wintypes.DWORD),
                ('biSizeImage', wintypes.DWORD),
                ('biXPelsPerMeter', ctypes.c_long),
                ('biYPelsPerMeter', ctypes.c_long),
                ('biClrUsed', wintypes.DWORD),
                ('biClrImportant', wintypes.DWORD),
            ]

        bmi = BITMAPINFOHEADER()
        bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.biPlanes = 1
        bmi.biBitCount = 32
        bmi.biWidth = width
        bmi.biHeight = -height

        buf = (ctypes.c_ubyte * (width * height * 4))()
        _gdi32.GetDIBits(mfc_dc, 0, 0, height, ctypes.byref(buf), ctypes.byref(bmi), 0)
        return bytes(buf)


class WindowsBitBltScreenshotService(ScreenshotService):
    """使用 BitBlt 抓桌面矩形区域。"""

    @property
    def method_name(self) -> str:
        return 'bitblt'

    def is_available(self) -> bool:
        return True

    def capture(self, rect: Rect) -> MatLike | None:
        try:
            screen_dc = _user32.GetDC(0)
            if not screen_dc:
                return None
            try:
                mfc_dc = _gdi32.CreateCompatibleDC(screen_dc)
                if not mfc_dc:
                    return None
                try:
                    w = int(rect.width)
                    h = int(rect.height)
                    save_bitmap = _gdi32.CreateDIBSection(mfc_dc, ctypes.byref(self._bitmap_info(w, h)), 0, None, 0, 0)
                    if not save_bitmap:
                        return None
                    try:
                        prev_obj = _gdi32.SelectObject(mfc_dc, save_bitmap)
                        try:
                            SRCCOPY = 0x00CC0020
                            ok = _gdi32.BitBlt(mfc_dc, 0, 0, w, h, screen_dc, int(rect.x1), int(rect.y1), SRCCOPY)
                            if not ok:
                                return None
                            buf = WindowsPrintWindowScreenshotService._extract_bitmap(mfc_dc, w, h)
                            return np.frombuffer(buf, dtype=np.uint8).reshape(h, w, 4)[:, :, :3].copy()
                        finally:
                            _gdi32.SelectObject(mfc_dc, prev_obj)
                    finally:
                        _gdi32.DeleteObject(save_bitmap)
                finally:
                    _gdi32.DeleteDC(mfc_dc)
            finally:
                _user32.ReleaseDC(0, screen_dc)
        except Exception:
            return None

    @staticmethod
    def _bitmap_info(width: int, height: int):
        class BITMAPINFOHEADER(ctypes.Structure):
            _fields_ = [
                ('biSize', wintypes.DWORD),
                ('biWidth', ctypes.c_long),
                ('biHeight', ctypes.c_long),
                ('biPlanes', wintypes.WORD),
                ('biBitCount', wintypes.WORD),
                ('biCompression', wintypes.DWORD),
                ('biSizeImage', wintypes.DWORD),
                ('biXPelsPerMeter', ctypes.c_long),
                ('biYPelsPerMeter', ctypes.c_long),
                ('biClrUsed', wintypes.DWORD),
                ('biClrImportant', wintypes.DWORD),
            ]

        class BITMAPINFO(ctypes.Structure):
            _fields_ = [
                ('bmiHeader', BITMAPINFOHEADER),
                ('bmiColors', wintypes.DWORD * 3),
            ]

        info = BITMAPINFO()
        info.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        info.bmiHeader.biWidth = width
        info.bmiHeader.biHeight = -height
        info.bmiHeader.biPlanes = 1
        info.bmiHeader.biBitCount = 32
        info.bmiHeader.biCompression = 0
        return info
