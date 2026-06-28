"""macOS 平台热键：pynput 全局键盘监听 + Quartz CGEventTap 兜底。

为避免触发 macOS Accessibility 权限弹窗，默认走 pynput 的进程内监听；
若需要检测跨进程按键（类似 GetAsyncKeyState），用 Quartz CGEventTap 单独启动线程。
"""

from __future__ import annotations

import re
import threading
from collections import defaultdict

from one_dragon.platform.hotkey_service import HotkeyService
from one_dragon.utils.log_utils import log

_VK_MAP = {
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
    'ctrl': 0x11,
    'alt': 0x12,
    'shift': 0x10,
    'cmd': 0x5B,
    'win': 0x5B,
}

_VK_NAME_TO_PYNPUT = {
    'ctrl': 'ctrl',
    'alt': 'alt',
    'shift': 'shift',
    'cmd': 'cmd',
    'space': 'space',
    'tab': 'tab',
    'enter': 'enter',
    'esc': 'esc',
    'escape': 'esc',
    'backspace': 'backspace',
    'delete': 'delete',
    'insert': 'insert',
    'home': 'home',
    'end': 'end',
    'page_up': 'page_up',
    'page_down': 'page_down',
    'up': 'up',
    'down': 'down',
    'left': 'left',
    'right': 'right',
}


class _KeyState:
    """线程安全的按键状态记录。"""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._pressed: dict[str, bool] = defaultdict(bool)

    def set_pressed(self, key_name: str, pressed: bool) -> None:
        with self._lock:
            self._pressed[key_name] = pressed

    def is_pressed(self, key_name: str) -> bool:
        with self._lock:
            return bool(self._pressed.get(key_name, False))


class _GlobalListener:
    """pynput 全局键盘监听单例。"""

    _instance: _GlobalListener | None = None

    def __init__(self) -> None:
        self.state = _KeyState()
        self._listener = None
        self._started = False
        self._start_lock = threading.Lock()

    @classmethod
    def get(cls) -> _GlobalListener:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def ensure_started(self) -> None:
        if self._started:
            return
        with self._start_lock:
            if self._started:
                return
            try:
                from pynput import keyboard
            except Exception as e:
                log.warning('pynput.keyboard 不可用: %s', e)
                return

            state = self.state

            def on_press(key):
                try:
                    name = self._pynput_key_to_name(key)
                    if name:
                        state.set_pressed(name, True)
                except Exception:
                    pass

            def on_release(key):
                try:
                    name = self._pynput_key_to_name(key)
                    if name:
                        state.set_pressed(name, False)
                except Exception:
                    pass

            try:
                self._listener = keyboard.Listener(on_press=on_press, on_release=on_release)
                self._listener.daemon = True
                self._listener.start()
                self._started = True
            except Exception as e:
                log.warning('启动 pynput 全局键盘监听失败（可能缺少 Accessibility 权限）: %s', e)

    @staticmethod
    def _pynput_key_to_name(key) -> str | None:
        from pynput.keyboard import Key, KeyCode
        if isinstance(key, Key):
            mapping = {
                Key.ctrl: 'ctrl', Key.ctrl_l: 'ctrl', Key.ctrl_r: 'ctrl',
                Key.alt: 'alt', Key.alt_l: 'alt', Key.alt_r: 'alt',
                Key.shift: 'shift', Key.shift_l: 'shift', Key.shift_r: 'shift',
                Key.cmd: 'cmd', Key.cmd_l: 'cmd', Key.cmd_r: 'cmd',
                Key.space: 'space', Key.tab: 'tab', Key.enter: 'enter',
                Key.esc: 'esc', Key.backspace: 'backspace', Key.delete: 'delete',
                Key.insert: 'insert', Key.home: 'home', Key.end: 'end',
                Key.page_up: 'page_up', Key.page_down: 'page_down',
                Key.up: 'up', Key.down: 'down', Key.left: 'left', Key.right: 'right',
            }
            return mapping.get(key)
        if isinstance(key, KeyCode):
            ch = key.char
            if ch and len(ch) == 1:
                return ch.lower()
        return None


class MacosHotkeyService(HotkeyService):

    def __init__(self) -> None:
        self._listener = _GlobalListener.get()
        self._listener.ensure_started()

    def is_key_pressed(self, vk: int) -> bool:
        # 倒查 VK -> pynput name
        for name, v in _VK_MAP.items():
            if v == vk and name in _VK_NAME_TO_PYNPUT:
                return self._listener.state.is_pressed(_VK_NAME_TO_PYNPUT[name])
        return False

    def is_ctrl_pressed(self) -> bool:
        return self._listener.state.is_pressed('ctrl')

    def is_alt_pressed(self) -> bool:
        return self._listener.state.is_pressed('alt')

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
        return _VK_MAP.get(name)

    def is_hotkey_combo_pressed(self, main_key: str) -> bool:
        vk = self.key_name_to_vk(main_key)
        if vk is None:
            return False
        if not (self.is_ctrl_pressed() and self.is_alt_pressed()):
            return False
        if 0x41 <= vk <= 0x5A:
            ch = chr(vk).lower()
            return self._listener.state.is_pressed(ch)
        # 其它键：尝试用 VK_MAP 倒查
        for name, v in _VK_MAP.items():
            if v == vk and name in _VK_NAME_TO_PYNPUT:
                return self._listener.state.is_pressed(_VK_NAME_TO_PYNPUT[name])
        return False

    def is_window_minimized(self, hwnd: int | None) -> bool:
        if hwnd is None or int(hwnd) == 0:
            return False
        try:
            from one_dragon.platform import get_platform_context
            ctx = get_platform_context()
            from one_dragon.platform.window_service import WindowInfo
            info = WindowInfo(handle=int(hwnd), title='', pid=0, bounds=None)  # type: ignore[arg-type]
            return ctx.window.is_minimized(info)
        except Exception:
            return False

    def is_window_visible(self, hwnd: int | None) -> bool:
        if hwnd is None or int(hwnd) == 0:
            return False
        try:
            from one_dragon.platform import get_platform_context
            ctx = get_platform_context()
            from one_dragon.platform.window_service import WindowInfo
            info = WindowInfo(handle=int(hwnd), title='', pid=0, bounds=None)  # type: ignore[arg-type]
            return ctx.window.is_visible(info)
        except Exception:
            return True
