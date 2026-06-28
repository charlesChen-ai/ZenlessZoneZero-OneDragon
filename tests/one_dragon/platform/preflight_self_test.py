"""平台层自测：用 PySide6 创建一个已知窗口，验证 platform layer 能否找到、截图、点击。

用法：
  PYTHONPATH=src /path/to/venv/bin/python tests/one_dragon/platform/preflight_self_test.py

预期：弹出 600x400 的测试窗口（左半红 / 右半黄），5 秒后脚本会尝试点击 4 个角点
      并截图，结果写入 /tmp/od_preflight_*.png。
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QApplication, QWidget


WINDOW_TITLE = "OD Pre-flight Self Test"
WINDOW_W = 600
WINDOW_H = 400
OUTPUT_DIR = Path("/tmp")


class TestWindow(QWidget):

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(WINDOW_W, WINDOW_H)
        self.clicks_received: list[tuple[int, int]] = []

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.fillRect(0, 0, self.width() // 2, self.height(), QColor(220, 60, 60))
        p.fillRect(self.width() // 2, 0, self.width() // 2, self.height(), QColor(240, 200, 60))
        p.setPen(QColor(255, 255, 255))
        p.drawText(20, 30, f"OD preflight — click me!")

    def mousePressEvent(self, event) -> None:
        pos = event.position()
        self.clicks_received.append((int(pos.x()), int(pos.y())))
        print(f"  [TestWindow] click at ({int(pos.x())}, {int(pos.y())})", flush=True)


def main() -> int:
    app = QApplication(sys.argv)
    win = TestWindow()
    win.show()
    win.raise_()
    win.activateWindow()

    # Force event processing so the window appears on screen
    for _ in range(10):
        app.processEvents()
        time.sleep(0.1)

    # Import platform layer AFTER QApplication (so it sees real windows)
    from one_dragon.platform import get_platform_context
    from one_dragon.base.geometry.rectangle import Rect

    ctx = get_platform_context()
    print(f"Platform: {ctx.name}")
    print(f"Window object: {type(win).__name__}")
    print()

    # Phase 1: Find the window
    print("=== Phase 1: 找窗口 ===")
    info = None
    for attempt in range(20):
        info = ctx.window.find_by_title(WINDOW_TITLE)
        if info is not None:
            break
        time.sleep(0.2)
        app.processEvents()
    if info is None:
        print(f"  ❌ 找不到标题为 '{WINDOW_TITLE}' 的窗口")
        print("  列出所有 owner 包含 PySide/Qt 的窗口:")
        for w in ctx.window.list_windows():
            if w.title and 'preflight' in w.title.lower():
                print(f"    [匹配] {w.title!r} @ {w.bounds}")
            elif w.title and ('preflight' in w.title.lower() or 'test' in w.title.lower()):
                print(f"    [候选] {w.title!r} @ {w.bounds}")
        # show all
        print("  所有可见窗口:")
        for w in ctx.window.list_windows()[:20]:
            print(f"    {w.title!r} @ {w.bounds}")
        return 1
    print(f"  ✓ 找到窗口 handle={info.handle} bounds={info.bounds}")

    # Wait for window to be fully drawn
    time.sleep(1.0)

    # Phase 2: Capture the window
    print("\n=== Phase 2: 截图 ===")
    img = ctx.screenshot.capture(info.bounds)
    if img is None:
        print("  ❌ 截图返回 None")
        return 1
    import cv2
    import numpy as np
    print(f"  ✓ 截图 shape={img.shape}")
    # Check left half (red) and right half (yellow)
    left_mean = img[:, :WINDOW_W // 2, :].mean(axis=(0, 1))
    right_mean = img[:, WINDOW_W // 2:, :].mean(axis=(0, 1))
    print(f"  左半平均色 (期望 R 高): R={left_mean[0]:.0f} G={left_mean[1]:.0f} B={left_mean[2]:.0f}")
    print(f"  右半平均色 (期望 R+G 高): R={right_mean[0]:.0f} G={right_mean[1]:.0f} B={right_mean[2]:.0f}")
    if left_mean[0] > left_mean[2] + 30 and right_mean[0] > 150 and right_mean[1] > 150:
        print("  ✓ 颜色匹配预期 (左红右黄)")
    else:
        print(f"  ⚠️  颜色不完全匹配 (可能区域选择 / 屏幕缩放 / 权限问题)")

    out = OUTPUT_DIR / "od_preflight_full.png"
    cv2.imwrite(str(out), cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    print(f"  ✓ 保存 {out}")

    # Phase 3: Click 4 corners and verify clicks are received
    print("\n=== Phase 3: 点击 4 个角点 ===")
    corners = [
        ("左上 (50, 50)", 50, 50),
        ("右上 (W-50, 50)", WINDOW_W - 50, 50),
        ("左下 (50, H-50)", 50, WINDOW_H - 50),
        ("右下 (W-50, H-50)", WINDOW_W - 50, WINDOW_H - 50),
    ]
    for label, gx, gy in corners:
        mapped = ctx.window.client_to_screen(info, gx, gy)
        if mapped is None:
            print(f"  ⚠️  {label}: client_to_screen 失败")
            continue
        sx, sy = mapped
        print(f"  {label}: game=({gx},{gy}) -> screen=({sx},{sy})")
        ctx.input.move_to(sx, sy)
        time.sleep(0.2)
        ctx.input.click(sx, sy)
        time.sleep(0.5)

    # Phase 4: Capture again and verify clicks were received
    print("\n=== Phase 4: 收尾 ===")
    time.sleep(0.5)
    print(f"  窗口收到点击数: {len(win.clicks_received)}")
    for c in win.clicks_received:
        print(f"    {c}")

    if len(win.clicks_received) == 4:
        print("\n✅ 所有 4 次点击都被窗口接收 (pynput 鼠标事件正常)")
        return 0
    else:
        print(f"\n❌ 只收到 {len(win.clicks_received)}/4 次点击")
        print("   常见原因:")
        print("   - macOS 隐私与安全 > 辅助功能 未授权 Terminal/iTerm")
        print("   - 窗口被其他窗口遮挡")
        print("   - 权限问题：参考 docs/develop/guides/mac_cloud_porting.md")
        return 2


if __name__ == "__main__":
    rc = main()
    sys.exit(rc)
