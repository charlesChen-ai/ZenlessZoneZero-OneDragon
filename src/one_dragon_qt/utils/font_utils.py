"""
跨平台 UI 字体工具
根据当前操作系统返回合适的中文 UI 字体。
"""
from __future__ import annotations

from PySide6.QtGui import QFont


def get_ui_font(size: int, bold: bool = False) -> QFont:
    """
    获取适合当前操作系统的 UI 字体。

    - Windows: Microsoft YaHei
    - macOS: PingFang SC (回退 Hiragino Sans GB / Heiti SC)
    - Linux: Noto Sans CJK SC (回退 WenQuanYi Micro Hei)

    Args:
        size: 字号
        bold: 是否加粗
    """
    try:
        from one_dragon.platform.context import is_macos, is_windows
        if is_macos():
            family = 'PingFang SC'
        elif is_windows():
            family = 'Microsoft YaHei'
        else:
            family = 'Noto Sans CJK SC'
    except ImportError:
        # 兜底:用 sys.platform
        import sys
        if sys.platform == 'darwin':
            family = 'PingFang SC'
        elif sys.platform == 'win32':
            family = 'Microsoft YaHei'
        else:
            family = 'Noto Sans CJK SC'

    font = QFont(family, size)
    if bold:
        font.setBold(True)
    return font
