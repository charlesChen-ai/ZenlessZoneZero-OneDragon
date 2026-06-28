"""
非 Windows 平台使用的占位 Controller。
所有操作都是 NoOp,用于在 mac/linux 上让 ZContext 实例化通过,业务模块可 import。
"""
from __future__ import annotations

from cv2.typing import MatLike

from one_dragon.base.controller.controller_base import ControllerBase
from one_dragon.base.geometry.point import Point


class MockController(ControllerBase):
    """占位 Controller,所有操作返回安全默认值。

    仅用于非 Windows 平台让 ZContext 可以实例化、GUI 可启动。
    业务侧调用 click / screenshot / scroll 等不会真正生效。
    """

    def __init__(self):
        super().__init__()

    def init_before_context_run(self) -> bool:
        return True

    def click(self, pos: Point = None, press_time: float = 0, pc_alt: bool = False, gamepad_key: str | None = None) -> bool:
        return False

    def get_screenshot(self, independent: bool = False) -> MatLike | None:
        return None

    def fill_uid_black(self, screen: MatLike) -> MatLike:
        return screen
