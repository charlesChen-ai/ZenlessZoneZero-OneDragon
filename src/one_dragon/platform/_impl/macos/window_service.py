"""macOS 平台窗口服务：基于 Quartz.CGWindowListCopyWindowInfo。"""

from __future__ import annotations

from one_dragon.base.geometry.rectangle import Rect
from one_dragon.platform.window_service import WindowInfo, WindowService
from one_dragon.utils.log_utils import log

try:
    from AppKit import NSWorkspace
    from Quartz import (
        CGWindowListCopyWindowInfo,
        kCGNullWindowID,
        kCGWindowListOptionOnScreenOnly,
    )
except ImportError as e:  # pragma: no cover - 仅在非 macOS 加载
    CGWindowListCopyWindowInfo = None
    kCGWindowListOptionOnScreenOnly = 1 << 0
    kCGNullWindowID = 0
    NSWorkspace = None
    _IMPORT_ERROR = e
else:
    _IMPORT_ERROR = None


def _require_quartz():
    if CGWindowListCopyWindowInfo is None:
        raise RuntimeError(f'macOS 平台需要安装 pyobjc-framework-Quartz / -Cocoa: {_IMPORT_ERROR}')


class MacosWindowService(WindowService):

    def _list_raw(self) -> list[dict]:
        _require_quartz()
        opts = kCGWindowListOptionOnScreenOnly
        windows = CGWindowListCopyWindowInfo(opts, kCGNullWindowID) or []
        return list(windows)

    def list_windows(self) -> list[WindowInfo]:
        result: list[WindowInfo] = []
        for w in self._list_raw():
            info = self._to_window_info(w)
            if info is not None:
                result.append(info)
        return result

    def find_by_title(self, title: str) -> WindowInfo | None:
        for w in self._list_raw():
            name = w.get('kCGWindowName') or ''
            if name == title:
                info = self._to_window_info(w)
                if info is not None:
                    return info
        return None

    def find_by_title_contains(self, substring: str) -> list[WindowInfo]:
        out: list[WindowInfo] = []
        for w in self._list_raw():
            name = w.get('kCGWindowName') or ''
            if substring and substring in name:
                info = self._to_window_info(w)
                if info is not None:
                    out.append(info)
        return out

    def get_window_bounds(self, info: WindowInfo) -> Rect | None:
        return info.bounds

    def get_client_rect(self, info: WindowInfo) -> Rect | None:
        # Quartz 的 Bounds 已经是包含内容区的窗口外框（不含标题栏之外的内容）。
        # 对于流式窗口，kCGWindowBounds 已经是 client area。
        return info.bounds

    def client_to_screen(self, info: WindowInfo, x: int, y: int) -> tuple[int, int] | None:
        if info.bounds is None:
            return None
        return info.bounds.x1 + int(x), info.bounds.y1 + int(y)

    def screen_to_client(self, info: WindowInfo, x: int, y: int) -> tuple[int, int] | None:
        if info.bounds is None:
            return None
        return int(x) - info.bounds.x1, int(y) - info.bounds.y1

    def is_window_valid(self, info: WindowInfo) -> bool:
        for w in self._list_raw():
            if int(w.get('kCGWindowNumber', -1)) == int(info.handle):
                return True
        return False

    def is_minimized(self, info: WindowInfo) -> bool:
        for w in self._list_raw():
            if int(w.get('kCGWindowNumber', -1)) == int(info.handle):
                layer = int(w.get('kCGWindowLayer', 0))
                alpha = float(w.get('kCGWindowAlpha', 1.0))
                bounds = w.get('kCGWindowBounds') or {}
                if bounds.get('Height', 0) == 0 or alpha == 0:
                    return True
                return layer < 0
        return False

    def is_visible(self, info: WindowInfo) -> bool:
        for w in self._list_raw():
            if int(w.get('kCGWindowNumber', -1)) == int(info.handle):
                alpha = float(w.get('kCGWindowAlpha', 0))
                return alpha > 0
        return False

    def restore(self, info: WindowInfo) -> bool:
        if not self.is_minimized(info):
            return True
        # macOS 上没有公开 API 取消最小化；交给用户手动或通过 AX 桥接。
        log.warning('macOS 上无法通过公开 API 自动恢复最小化窗口，请在系统手动恢复')
        return False

    def activate(self, info: WindowInfo) -> bool:
        _require_quartz()
        try:
            from AppKit import NSApp
            # 把进程提到前台
            NSApp.activateIgnoringOtherApps_(True)
            return True
        except Exception as e:
            log.warning('激活窗口失败: %s', e)
            return False

    def get_foreground(self) -> WindowInfo | None:
        _require_quartz()
        opts = kCGWindowListOptionOnScreenOnly
        # layer == 0 视作前台层
        for w in CGWindowListCopyWindowInfo(opts, kCGNullWindowID) or []:
            if int(w.get('kCGWindowLayer', -1)) == 0:
                info = self._to_window_info(w)
                if info is not None and info.title:
                    return info
        return None

    def set_foreground(self, info: WindowInfo) -> bool:
        return self.activate(info)

    @staticmethod
    def _to_window_info(raw: dict) -> WindowInfo | None:
        handle = int(raw.get('kCGWindowNumber', 0))
        if not handle:
            return None
        bounds_raw = raw.get('kCGWindowBounds') or {}
        x = float(bounds_raw.get('X', 0))
        y = float(bounds_raw.get('Y', 0))
        w = float(bounds_raw.get('Width', 0))
        h = float(bounds_raw.get('Height', 0))
        return WindowInfo(
            handle=handle,
            title=str(raw.get('kCGWindowName') or ''),
            pid=int(raw.get('kCGWindowOwnerPID', 0)),
            bounds=Rect(int(x), int(y), int(x + w), int(y + h)),
        )
