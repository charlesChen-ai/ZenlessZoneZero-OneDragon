"""未知平台兜底服务测试。"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

pytest.importorskip("cv2")

from one_dragon.base.geometry.rectangle import Rect


def test_fallback_input_click_does_not_raise(fake_pyautogui: MagicMock) -> None:
    from one_dragon.platform._impl.fallback_impl import FallbackInputService

    svc = FallbackInputService()
    svc.click(100, 100)

    fake_pyautogui.moveTo.assert_called_with(100, 100)


def test_fallback_input_click_right_button(fake_pyautogui: MagicMock) -> None:
    from one_dragon.platform._impl.fallback_impl import FallbackInputService

    svc = FallbackInputService()
    svc.click(50, 60, button="right", press_time=0.01)

    fake_pyautogui.moveTo.assert_called_with(50, 60)


def test_fallback_input_get_mouse_pos_returns_int_tuple(
    fake_pyautogui: MagicMock,
) -> None:
    from one_dragon.platform._impl.fallback_impl import FallbackInputService

    svc = FallbackInputService()
    pos = svc.get_mouse_pos()

    assert isinstance(pos, tuple)
    assert len(pos) == 2
    assert isinstance(pos[0], int)
    assert isinstance(pos[1], int)


def test_fallback_input_get_mouse_sensitivity_returns_int(
    fake_pyautogui: MagicMock,
) -> None:
    from one_dragon.platform._impl.fallback_impl import FallbackInputService

    svc = FallbackInputService()
    assert isinstance(svc.get_mouse_sensitivity(), int)


def test_fallback_input_move_methods_call_pyautogui(
    fake_pyautogui: MagicMock,
) -> None:
    from one_dragon.platform._impl.fallback_impl import FallbackInputService

    svc = FallbackInputService()
    svc.move_to(10, 20)
    svc.move_relative(5, 5)

    fake_pyautogui.moveTo.assert_called_with(10, 20)


def test_fallback_screenshot_capture_returns_array(
    fake_pyautogui: MagicMock,
    fake_screenshot_image,
) -> None:
    from one_dragon.platform._impl.fallback_impl import FallbackScreenshotService

    fake_pyautogui.screenshot.return_value = fake_screenshot_image
    svc = FallbackScreenshotService()

    result = svc.capture(Rect(0, 0, 100, 100))

    assert result is not None
    assert result.shape == (10, 10, 3)
    fake_pyautogui.screenshot.assert_called_with(region=(0, 0, 100, 100))


def test_fallback_screenshot_capture_returns_none_on_exception(
    fake_pyautogui: MagicMock,
) -> None:
    from one_dragon.platform._impl.fallback_impl import FallbackScreenshotService

    fake_pyautogui.screenshot.side_effect = RuntimeError("boom")
    svc = FallbackScreenshotService()

    assert svc.capture(Rect(0, 0, 100, 100)) is None


def test_fallback_screenshot_is_available(fake_pyautogui: MagicMock) -> None:
    from one_dragon.platform._impl.fallback_impl import FallbackScreenshotService

    assert FallbackScreenshotService().is_available() is True
    assert FallbackScreenshotService().method_name == "pil"


def test_fallback_clipboard_set_text(fake_pyautogui: MagicMock) -> None:
    from one_dragon.platform._impl.fallback_impl import FallbackClipboardService

    svc = FallbackClipboardService()
    svc.set_text("hello world")

    fake_pyautogui.write.assert_called_with("hello world", interval=0)


def test_fallback_clipboard_get_text_returns_str(
    fake_pyautogui: MagicMock,
) -> None:
    from one_dragon.platform._impl.fallback_impl import FallbackClipboardService

    svc = FallbackClipboardService()
    assert isinstance(svc.get_text(), str)


def test_fallback_clipboard_clear_does_not_raise(
    fake_pyautogui: MagicMock,
) -> None:
    from one_dragon.platform._impl.fallback_impl import FallbackClipboardService

    FallbackClipboardService().clear()


def test_fallback_clipboard_set_image_does_not_raise(
    fake_pyautogui: MagicMock,
) -> None:
    from one_dragon.platform._impl.fallback_impl import FallbackClipboardService

    FallbackClipboardService().set_image(MagicMock())


def test_noop_dialog_show_methods_do_not_raise(fake_messagebox: MagicMock) -> None:
    from one_dragon.platform._impl.fallback_impl import NoopDialogService

    svc = NoopDialogService()
    svc.show_error("t", "m")
    svc.show_warning("t", "m")
    svc.show_info("t", "m")


def test_noop_dialog_confirm_returns_bool(fake_messagebox: MagicMock) -> None:
    from one_dragon.platform._impl.fallback_impl import NoopDialogService

    svc = NoopDialogService()
    assert isinstance(svc.confirm("t", "m"), bool)


def test_fallback_window_service_returns_empty_and_none() -> None:
    from one_dragon.platform._impl.fallback_impl import FallbackWindowService

    svc = FallbackWindowService()
    assert svc.list_windows() == []
    assert svc.find_by_title("x") is None
    assert svc.find_by_title_contains("x") == []
