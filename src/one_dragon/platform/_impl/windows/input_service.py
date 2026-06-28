"""Windows 平台输入服务：pyautogui + pynput。"""

from __future__ import annotations

import ctypes

import pyautogui
from pynput.keyboard import Controller, Key

from one_dragon.platform.input_service import InputService


class WindowsInputService(InputService):

    def __init__(self) -> None:
        self._keyboard = Controller()
        pyautogui.PAUSE = 0.001
        pyautogui.FAILSAFE = False

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
        speed = self.get_mouse_sensitivity()
        unit = 2000 if speed <= 10 else 1000
        pyautogui.scroll(-unit * clicks, x, y)

    def key_tap(self, key: str) -> None:
        self._keyboard.tap(self._normalize_key(key))

    def key_press(self, key: str) -> None:
        self._keyboard.press(self._normalize_key(key))

    def key_release(self, key: str) -> None:
        self._keyboard.release(self._normalize_key(key))

    def hotkey(self, *keys: str) -> None:
        normalized = [self._normalize_key(k) for k in keys]
        with self._keyboard.pressed(*normalized[:-1]):
            self._keyboard.tap(normalized[-1])

    def type_text(self, text: str, interval: float = 0.1) -> None:
        self._keyboard.type(text)

    def get_mouse_pos(self) -> tuple[int, int]:
        pos = pyautogui.position()
        return int(pos.x), int(pos.y)

    def get_mouse_sensitivity(self) -> int:
        user32 = ctypes.windll.user32
        speed = ctypes.c_int()
        user32.SystemParametersInfoA(0x0070, 0, ctypes.byref(speed), 0)
        return int(speed.value)

    @staticmethod
    def _normalize_key(key: str):
        try:
            return Key[key]
        except KeyError:
            return key
