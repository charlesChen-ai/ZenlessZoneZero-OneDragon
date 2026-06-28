"""未知平台兜底实现：使用 pyautogui / pynput / tkinter。

适用于 macOS / Windows 之外的平台。功能极简。
"""

from __future__ import annotations

import pyautogui
from cv2.typing import MatLike

from one_dragon.base.geometry.rectangle import Rect
from one_dragon.platform.clipboard_service import ClipboardService
from one_dragon.platform.dialog_service import DialogService
from one_dragon.platform.hotkey_service import HotkeyService
from one_dragon.platform.input_service import InputService
from one_dragon.platform.overlay_service import OverlayService
from one_dragon.platform.screenshot_service import ScreenshotService
from one_dragon.platform.window_service import WindowInfo, WindowService


class FallbackWindowService(WindowService):
    def list_windows(self) -> list[WindowInfo]:
        return []

    def find_by_title(self, title: str) -> WindowInfo | None:
        return None

    def find_by_title_contains(self, substring: str) -> list[WindowInfo]:
        return []

    def get_window_bounds(self, info: WindowInfo) -> Rect | None:
        return None

    def get_client_rect(self, info: WindowInfo) -> Rect | None:
        return None

    def client_to_screen(self, info: WindowInfo, x: int, y: int) -> tuple[int, int] | None:
        return None

    def screen_to_client(self, info: WindowInfo, x: int, y: int) -> tuple[int, int] | None:
        return None

    def is_window_valid(self, info: WindowInfo) -> bool:
        return False

    def is_minimized(self, info: WindowInfo) -> bool:
        return False

    def is_visible(self, info: WindowInfo) -> bool:
        return False

    def restore(self, info: WindowInfo) -> bool:
        return False

    def activate(self, info: WindowInfo) -> bool:
        return False

    def get_foreground(self) -> WindowInfo | None:
        return None

    def set_foreground(self, info: WindowInfo) -> bool:
        return False


class FallbackInputService(InputService):
    def click(self, x: int, y: int, button: str = 'left', press_time: float = 0) -> None:
        btn = pyautogui.PRIMARY if button == 'left' else pyautogui.SECONDARY
        pyautogui.moveTo(x, y)
        pyautogui.mouseDown(button=btn)
        pyautogui.sleep(max(0.001, press_time))
        pyautogui.mouseUp(button=btn)

    def double_click(self, x: int, y: int, button: str = 'left') -> None:
        pyautogui.doubleClick(x, y, button=pyautogui.PRIMARY if button == 'left' else pyautogui.SECONDARY)

    def move_to(self, x: int, y: int) -> None:
        pyautogui.moveTo(x, y)

    def move_relative(self, dx: int, dy: int) -> None:
        if dx or dy:
            pyautogui.moveRel(dx, dy)

    def drag(self, sx: int, sy: int, ex: int, ey: int, duration: float = 0.5) -> None:
        pyautogui.moveTo(sx, sy)
        pyautogui.dragTo(ex, ey, duration=duration)

    def scroll(self, clicks: int, x: int | None = None, y: int | None = None) -> None:
        pyautogui.scroll(-clicks, x, y)

    def key_tap(self, key: str) -> None:
        pyautogui.press(key)

    def key_press(self, key: str) -> None:
        pyautogui.keyDown(key)

    def key_release(self, key: str) -> None:
        pyautogui.keyUp(key)

    def hotkey(self, *keys: str) -> None:
        pyautogui.hotkey(*keys)

    def type_text(self, text: str, interval: float = 0.1) -> None:
        pyautogui.typewrite(text, interval=interval) if text.isascii() else pyautogui.write(text, interval=interval)

    def get_mouse_pos(self) -> tuple[int, int]:
        pos = pyautogui.position()
        return int(pos.x), int(pos.y)

    def get_mouse_sensitivity(self) -> int:
        return 10


class FallbackScreenshotService(ScreenshotService):
    @property
    def method_name(self) -> str:
        return 'pil'

    def is_available(self) -> bool:
        return True

    def capture(self, rect: Rect) -> MatLike | None:
        try:
            img = pyautogui.screenshot(region=(rect.x1, rect.y1, rect.width, rect.height))
        except Exception:
            return None
        import numpy as np
        return np.array(img)


class FallbackClipboardService(ClipboardService):
    def set_text(self, text: str) -> None:
        pyautogui.write(text, interval=0)

    def get_text(self) -> str:
        return ''

    def clear(self) -> None:
        return None

    def set_image(self, image: MatLike) -> None:
        return None


class NoopOverlayService(OverlayService):
    def set_click_through(self, hwnd: int, enabled: bool) -> bool:
        return False

    def set_exclude_from_capture(self, hwnd: int, enabled: bool) -> bool:
        return False


class NoopHotkeyService(HotkeyService):
    def is_key_pressed(self, vk: int) -> bool:
        return False

    def is_ctrl_pressed(self) -> bool:
        return False

    def is_alt_pressed(self) -> bool:
        return False

    def key_name_to_vk(self, key: str) -> int | None:
        return None

    def is_hotkey_combo_pressed(self, main_key: str) -> bool:
        return False

    def is_window_minimized(self, hwnd: int | None) -> bool:
        return False

    def is_window_visible(self, hwnd: int | None) -> bool:
        return True


class _TkRoot:
    """延迟创建隐藏 tk root，用于 messagebox。"""

    _root = None

    @classmethod
    def get(cls):
        if cls._root is None:
            import tkinter as tk
            cls._root = tk.Tk()
            cls._root.withdraw()
        return cls._root


class NoopDialogService(DialogService):
    def show_error(self, title: str, message: str) -> None:
        try:
            from tkinter import messagebox
            _TkRoot.get()
            messagebox.showerror(title, message)
        except Exception:
            print(f'[ERROR] {title}: {message}')

    def show_warning(self, title: str, message: str) -> None:
        try:
            from tkinter import messagebox
            _TkRoot.get()
            messagebox.showwarning(title, message)
        except Exception:
            print(f'[WARN] {title}: {message}')

    def show_info(self, title: str, message: str) -> None:
        try:
            from tkinter import messagebox
            _TkRoot.get()
            messagebox.showinfo(title, message)
        except Exception:
            print(f'[INFO] {title}: {message}')

    def confirm(self, title: str, message: str) -> bool:
        try:
            from tkinter import messagebox
            _TkRoot.get()
            return bool(messagebox.askokcancel(title, message))
        except Exception:
            return False
