"""macOS 平台 Overlay：NSWindow.ignoresMouseEvents。

截图排除（NSWindowSharingNone）需要 macOS 14+ 私有符号；本实现先不启用。
"""

from __future__ import annotations

import contextlib

from one_dragon.platform.overlay_service import OverlayService
from one_dragon.utils.log_utils import log


class MacosOverlayService(OverlayService):

    def set_click_through(self, hwnd: int, enabled: bool) -> bool:
        if not hwnd:
            return False
        with contextlib.suppress(Exception):
            from PyObjC import _objc as objc_runtime  # noqa: F401
        try:
            from PyObjC import _objc as objc_runtime
            view = objc_runtime.ObjCObject(int(hwnd))
            window = view.window()
            if window is None:
                return False
            window.setIgnoresMouseEvents_(bool(enabled))
            return True
        except Exception as e:
            log.debug('设置 click_through 失败: %s', e)
            return False

    def set_exclude_from_capture(self, hwnd: int, enabled: bool) -> bool:
        if enabled:
            log.warning('macOS 不支持截图排除 (NSWindowSharingNone 私有 API)；忽略')
        return False
