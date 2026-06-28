"""平台无关的运行环境抽象层。

按职责拆出 8 个 service（窗口 / 输入 / 截图 / 剪贴板 / Overlay / Hotkey / 弹窗 / 控制台），
通过 :func:`get_platform_context` 获取当前平台的实现。
"""

from one_dragon.platform.context import (
    PlatformContext,
    get_platform_context,
    is_macos,
    is_windows,
)

__all__ = [
    'PlatformContext',
    'get_platform_context',
    'is_macos',
    'is_windows',
]
