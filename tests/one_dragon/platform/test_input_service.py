"""输入服务接口测试。"""

from __future__ import annotations

import contextlib
import ctypes
import sys
from unittest.mock import MagicMock

import pytest

pytest.importorskip("cv2")

from one_dragon.platform.context import get_platform_context
from one_dragon.platform.input_service import InputService


@pytest.fixture
def platform_input_service(
    fake_pyautogui: MagicMock,
    fake_pynput_keyboard: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> InputService:
    if sys.platform == "win32":
        def fake_system_parameters_info(a, b, ptr, d) -> int:
            with contextlib.suppress(AttributeError):
                ptr.contents.value = ctypes.c_int(15).value
            return 1

        fake_user32 = MagicMock(name="user32")
        fake_user32.SystemParametersInfoA.side_effect = fake_system_parameters_info
        monkeypatch.setattr("ctypes.windll.user32", fake_user32)
    get_platform_context.cache_clear()
    return get_platform_context().input


def test_platform_input_service_is_input_service(
    platform_input_service: InputService,
) -> None:
    assert isinstance(platform_input_service, InputService)


def test_platform_input_service_click_does_not_raise(
    platform_input_service: InputService,
) -> None:
    platform_input_service.click(100, 100)


def test_platform_input_service_click_with_button_does_not_raise(
    platform_input_service: InputService,
) -> None:
    platform_input_service.click(50, 60, button="right", press_time=0.01)


def test_platform_input_service_get_mouse_pos_returns_int_tuple(
    platform_input_service: InputService,
) -> None:
    pos = platform_input_service.get_mouse_pos()
    assert isinstance(pos, tuple)
    assert len(pos) == 2
    assert isinstance(pos[0], int)
    assert isinstance(pos[1], int)


def test_platform_input_service_get_mouse_sensitivity_returns_int(
    platform_input_service: InputService,
) -> None:
    sensitivity = platform_input_service.get_mouse_sensitivity()
    assert isinstance(sensitivity, int)


def test_platform_input_service_move_methods_do_not_raise(
    platform_input_service: InputService,
) -> None:
    platform_input_service.move_to(10, 20)
    platform_input_service.move_relative(5, 5)
