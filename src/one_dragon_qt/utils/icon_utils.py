"""
跨平台应用图标工具
"""
from __future__ import annotations

import os
import sys


def _has_png_logo() -> bool:
    """检查 assets/ui/logo.png 是否存在(跨平台 PNG 优先)。"""
    try:
        from one_dragon.utils.os_utils import get_resource_path
        png_path = get_resource_path('assets', 'ui', 'logo.png')
        return os.path.exists(png_path)
    except Exception:
        return False


def get_platform_app_icon() -> str | None:
    """
    返回当前平台适合的应用图标文件名。

    优先级:
    1. 跨平台 logo.png (若 assets/ui/logo.png 存在)— macOS / Linux 均可使用
    2. Windows logo.ico
    3. 其它平台返回 None
    """
    if _has_png_logo():
        return 'logo.png'
    if sys.platform == 'win32':
        return 'logo.ico'
    return None


def get_platform_card_logo_path() -> str | None:
    """
    返回安装器界面内嵌卡片 Logo 的资源相对路径。

    优先级同 get_platform_app_icon。
    """
    if _has_png_logo():
        return 'assets/ui/logo.png'
    if sys.platform == 'win32':
        return 'assets/ui/logo.ico'
    return None
