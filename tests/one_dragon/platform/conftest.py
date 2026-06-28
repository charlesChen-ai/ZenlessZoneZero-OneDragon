"""平台无关层测试 conftest：路径、GUI 跳过、依赖 mock。"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock

import pytest

ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def _is_headless() -> bool:
    if os.environ.get("CI") == "true":
        return True
    if os.environ.get("HEADLESS") == "1":
        return True
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        return True
    return False


requires_gui = pytest.mark.skipif(
    _is_headless(),
    reason="无显示器 / CI 环境，跳过需要真实 GUI 的用例",
)


@pytest.fixture
def require_gui() -> None:
    if _is_headless():
        pytest.skip("无显示器 / CI 环境")


class _FakePos:

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y


@pytest.fixture
def fake_pyautogui(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    fake = MagicMock(name="pyautogui")
    fake.PRIMARY = "left"
    fake.SECONDARY = "right"
    fake.FAILSAFE = False
    fake.position.return_value = _FakePos(42, 84)
    monkeypatch.setitem(sys.modules, "pyautogui", fake)
    for mod_name in (
            "one_dragon.platform._impl.fallback_impl",
            "one_dragon.platform._impl.macos.input_service",
            "one_dragon.platform._impl.macos.screenshot_service",
            "one_dragon.platform._impl.windows.input_service",
    ):
        mod = sys.modules.get(mod_name)
        if mod is not None and hasattr(mod, "pyautogui"):
            monkeypatch.setattr(mod, "pyautogui", fake)
    return fake


@pytest.fixture
def fake_pynput_keyboard(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    fake_key = MagicMock(name="pynput.keyboard.Key")
    fake_key.__getitem__.side_effect = lambda name: name
    fake_controller = MagicMock(name="pynput.keyboard.Controller")
    fake_keyboard = MagicMock(name="pynput.keyboard")
    fake_keyboard.Key = fake_key
    fake_keyboard.Controller = fake_controller
    fake_pynput = ModuleType("pynput")
    fake_pynput.keyboard = fake_keyboard
    monkeypatch.setitem(sys.modules, "pynput", fake_pynput)
    monkeypatch.setitem(sys.modules, "pynput.keyboard", fake_keyboard)
    for mod_name in (
            "one_dragon.platform._impl.macos.input_service",
            "one_dragon.platform._impl.windows.input_service",
    ):
        mod = sys.modules.get(mod_name)
        if mod is not None:
            if hasattr(mod, "Controller"):
                monkeypatch.setattr(mod, "Controller", fake_controller)
            if hasattr(mod, "Key"):
                monkeypatch.setattr(mod, "Key", fake_key)
    return fake_keyboard


class _ArrayableImage:

    def __init__(self, shape: tuple[int, ...]) -> None:
        self._shape = shape

    def __array__(self, dtype=None):
        import numpy as np
        return np.zeros(self._shape, dtype=dtype or np.uint8)


@pytest.fixture
def fake_screenshot_image() -> _ArrayableImage:
    return _ArrayableImage((10, 10, 3))


@pytest.fixture
def fake_messagebox(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    try:
        import tkinter.messagebox as mb
    except ImportError:
        pytest.skip("当前 Python 无 _tkinter，无法测试 NoopDialogService")
    fake = MagicMock(name="tkinter.messagebox")
    fake.showerror = MagicMock()
    fake.showwarning = MagicMock()
    fake.showinfo = MagicMock()
    fake.askokcancel = MagicMock(return_value=True)
    monkeypatch.setattr(mb, "showerror", fake.showerror)
    monkeypatch.setattr(mb, "showwarning", fake.showwarning)
    monkeypatch.setattr(mb, "showinfo", fake.showinfo)
    monkeypatch.setattr(mb, "askokcancel", fake.askokcancel)
    return fake


@pytest.fixture(autouse=True)
def _reset_platform_context_cache():
    try:
        from one_dragon.platform.context import get_platform_context
    except ImportError:
        yield
        return
    get_platform_context.cache_clear()
    yield
    get_platform_context.cache_clear()
