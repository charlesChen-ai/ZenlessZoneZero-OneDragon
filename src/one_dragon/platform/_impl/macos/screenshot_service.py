"""macOS 平台截图服务。"""

from __future__ import annotations

import cv2
import numpy as np
from cv2.typing import MatLike
from mss.base import MSSBase

from one_dragon.base.geometry.rectangle import Rect
from one_dragon.platform.screenshot_service import ScreenshotService


class MacosMssScreenshotService(ScreenshotService):
    """使用 mss 抓桌面区域。"""

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


class MacosPilScreenshotService(ScreenshotService):
    """使用 pyautogui 截图（macOS 走 Quartz 内部）。"""

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


class MacosQuartzScreenshotService(ScreenshotService):
    """使用 Quartz.CGWindowListCreateImage 抓指定 CGWindowID。

    对云游戏客户端这类可能用 DComp / Metal 直接渲染的窗口更稳定。
    需要 macOS 屏幕录制权限。
    """

    def __init__(self) -> None:
        self._checked_permission = False
        self._has_permission = False

    @property
    def method_name(self) -> str:
        return 'quartz_window'

    def is_available(self) -> bool:
        if not self._checked_permission:
            try:
                from Quartz import CGRequestScreenCaptureAccess
                self._has_permission = bool(CGRequestScreenCaptureAccess())
            except Exception:
                self._has_permission = False
            self._checked_permission = True
        return self._has_permission

    def capture(self, rect: Rect) -> MatLike | None:
        if not self.is_available():
            return None
        hwnd = getattr(rect, 'hwnd', 0)
        if not hwnd:
            return None
        try:
            from CoreFoundation import CFRelease
            from Quartz import (
                CGRectNull,
                CGWindowListCreateImage,
                kCGWindowImageBoundsIgnoreFraming,
                kCGWindowListOptionIncludingWindow,
            )
            cg_rect = CGRectNull  # 整窗
            image_ref = CGWindowListCreateImage(
                cg_rect,
                kCGWindowListOptionIncludingWindow,
                int(hwnd),
                kCGWindowImageBoundsIgnoreFraming,
            )
            if image_ref is None:
                return None
            try:
                from Quartz import (
                    CGDataProviderCopyData,
                    CGImageGetDataProvider,
                    CGImageGetHeight,
                    CGImageGetWidth,
                )
                width = int(CGImageGetWidth(image_ref))
                height = int(CGImageGetHeight(image_ref))
                provider = CGImageGetDataProvider(image_ref)
                data = CGDataProviderCopyData(provider)
                arr = np.frombuffer(bytes(data), dtype=np.uint8).reshape(height, width, 4)
                rgb = arr[:, :, :3].copy()
                return cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)  # Quartz 是 BGRA，去掉 A 后按 BGR->RGB
            finally:
                CFRelease(image_ref)
        except Exception:
            return None
