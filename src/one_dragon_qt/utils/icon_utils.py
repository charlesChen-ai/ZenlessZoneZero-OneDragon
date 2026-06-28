"""
跨平台应用图标工具
"""
from __future__ import annotations

import sys


def get_platform_app_icon() -> str | None:
    """
    返回当前平台适合的应用图标文件名。

    - Windows: 'logo.ico'
    - macOS / Linux: None(不设图标,后续可新增 logo.png)
    """
    if sys.platform == 'win32':
        return 'logo.ico'
    return None


def get_platform_card_logo_path() -> str | None:
    """
    返回安装器界面内嵌卡片 Logo 的资源相对路径。

    - Windows: 'assets/ui/logo.ico'
    - macOS / Linux: None(未提供 logo.png,跳过卡片 logo)
    """
    if sys.platform == 'win32':
        return 'assets/ui/logo.ico'
    return None
