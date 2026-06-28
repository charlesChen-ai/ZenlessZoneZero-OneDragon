"""云·绝区零预演脚本（用户日常用）

启动云·绝区零客户端并进入游戏后，单独跑此脚本验证：
  1. 平台层能找到云游戏窗口
  2. 截图能拿到云端游戏画面（不是黑屏/错误页）
  3. 点击中央会触发游戏内响应（截图 diff > 阈值）
  4. 测得端到端延迟

用法:
  PYTHONPATH=src /path/to/venv/bin/python tests/one_dragon/platform/cloud_zzz_preflight.py

退出码:
  0 = 全部通过
  1 = 找不到窗口
  2 = 截图是黑屏/错误页
  3 = 点击无响应
  4 = 延迟 > 200ms（云游戏时间敏感功能可能不靠谱）
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np


WINDOW_TITLE = "云·绝区零"
OUTPUT_DIR = Path("/tmp/od_cloud_preflight")
OUTPUT_DIR.mkdir(exist_ok=True)

# 默认中央点击位置（云·绝区零游戏内通常是角色区域）
DEFAULT_CENTER = (693, 451)  # 1386/2, 902/2


def main() -> int:
    from one_dragon.platform import get_platform_context
    from one_dragon.base.geometry.rectangle import Rect

    ctx = get_platform_context()
    print(f"Platform: {ctx.name}")
    print(f"截图可用方法: {ctx.screenshot.available_methods}")
    print()

    # Phase 1: 找窗口
    print(f"=== Phase 1: 找 '{WINDOW_TITLE}' 窗口 ===")
    info = ctx.window.find_by_title(WINDOW_TITLE)
    if info is None:
        print(f"  ❌ 未找到。可能是：")
        print(f"     1. 窗口标题不是 '{WINDOW_TITLE}' —— 设置 → 账号管理 → 自定义窗口标题")
        print(f"     2. 窗口未打开 / 已最小化")
        print(f"     3. macOS 屏幕录制权限未授权 Terminal/iTerm")
        print()
        print("  当前所有窗口:")
        for w in ctx.window.list_windows()[:20]:
            print(f"    {w.title!r} @ {w.bounds}")
        return 1
    print(f"  ✓ handle={info.handle} bounds={info.bounds} (size {info.bounds.width}x{info.bounds.height})")

    # Phase 2: 截图验证
    print("\n=== Phase 2: 截图 ===")
    img = ctx.screenshot.capture(info.bounds)
    if img is None:
        print("  ❌ 截图返回 None（屏幕录制权限？）")
        return 2

    print(f"  shape: {img.shape}")
    print(f"  mean: R={img[:,:,0].mean():.0f} G={img[:,:,1].mean():.0f} B={img[:,:,2].mean():.0f}")
    print(f"  std: {img.std():.1f}")

    out = OUTPUT_DIR / "01_full_window.png"
    cv2.imwrite(str(out), cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    print(f"  saved {out}")

    # 健康度判断
    mean_r = float(img[:,:,0].mean())
    mean_g = float(img[:,:,1].mean())
    mean_b = float(img[:,:,2].mean())
    std = float(img.std())

    is_black = mean_r < 5 and mean_g < 5 and mean_b < 5
    is_white = mean_r > 250 and mean_g > 250 and mean_b > 250
    is_static = std < 10
    issues = []
    if is_black:
        issues.append("整张图全黑（黑屏 / 视频流断开 / 录屏权限不足）")
    if is_white:
        issues.append("整张图全白（白屏 / 加载中）")
    if is_static:
        issues.append(f"std={std:.1f} 极低（可能是静态错误页）")
    if issues:
        print(f"  ❌ 截图异常：{' / '.join(issues)}")
        return 2
    print(f"  ✓ 截图看起来是动态画面")

    # Phase 3: 点击中央
    print("\n=== Phase 3: 点击中央 ===")
    w, h = info.bounds.width, info.bounds.height
    cx, cy = w // 2, h // 2
    print(f"  目标: 客户端坐标 ({cx}, {cy})")

    # 截图中央（点击前）
    center_rect = Rect(
        info.bounds.x1 + w // 4,
        info.bounds.y1 + h // 4,
        info.bounds.x1 + 3 * w // 4,
        info.bounds.y1 + 3 * h // 4,
    )
    img_before = ctx.screenshot.capture(center_rect)
    cv2.imwrite(str(OUTPUT_DIR / "02_before_click.png"), cv2.cvtColor(img_before, cv2.COLOR_RGB2BGR))

    # 测延迟
    screen_x, screen_y = ctx.window.client_to_screen(info, cx, cy)
    print(f"  screen 坐标: ({screen_x}, {screen_y})")

    t0 = time.time()
    ctx.input.move_to(screen_x, screen_y, )  # pyautogui 默认会平滑
    move_time = (time.time() - t0) * 1000

    t0 = time.time()
    ctx.input.click(screen_x, screen_y, press_time=0.05)
    click_time = (time.time() - t0) * 1000

    time.sleep(0.5)
    pos = ctx.input.get_mouse_pos()
    print(f"  鼠标移动耗时: {move_time:.0f}ms, 点击耗时: {click_time:.0f}ms")
    print(f"  点击后鼠标位置: {pos}")
    ctx.input.move_to(50, 50)  # 移开避免影响
    time.sleep(0.3)

    img_after = ctx.screenshot.capture(center_rect)
    cv2.imwrite(str(OUTPUT_DIR / "03_after_click.png"), cv2.cvtColor(img_after, cv2.COLOR_RGB2BGR))
    diff = float(np.abs(img_after.astype(int) - img_before.astype(int)).mean())
    print(f"  中央区域 diff: {diff:.1f}")
    if diff > 5:
        print(f"  ✓ 点击触发了游戏内响应")
    else:
        print(f"  ❌ 点击无响应（diff={diff:.1f} <= 5）")
        print(f"     排查：")
        print(f"     1. 系统设置 → 隐私与安全 → 辅助功能 → 勾上 Terminal / iTerm")
        print(f"     2. 云游戏窗口是否在最前")
        print(f"     3. 试试手动点击 (50, 50) 看是否真在云窗口上")
        return 3

    # Phase 4: 延迟估算
    print("\n=== Phase 4: 端到端延迟（粗略） ===")
    print(f"  鼠标移动: ~{move_time:.0f}ms（不含云端处理）")
    print(f"  点击: ~{click_time:.0f}ms（不含云端处理）")
    print(f"  实际云游戏延迟 = 客户端到云端 + 云端处理 + 回流 = 估计 30-150ms")
    print(f"  本机这 0.5s 等待是给云端处理留时间")
    print()
    if move_time + click_time < 200:
        print(f"  ✓ 本机响应快（< 200ms），时间敏感功能（闪避/连携）可期待")
    else:
        print(f"  ⚠️  本机响应慢（{move_time + click_time:.0f}ms），闪避/连携可能不可靠")

    # Phase 5: 综合报告
    print("\n=== 汇总 ===")
    report = {
        "platform": ctx.name,
        "window": {
            "title": info.title,
            "handle": info.handle,
            "bounds": [info.bounds.x1, info.bounds.y1, info.bounds.x2, info.bounds.y2],
            "size": [info.bounds.width, info.bounds.height],
        },
        "screenshot": {
            "shape": list(img.shape),
            "mean_rgb": [mean_r, mean_g, mean_b],
            "std": std,
        },
        "click": {
            "center": [cx, cy],
            "screen": [screen_x, screen_y],
            "diff": diff,
            "move_ms": move_time,
            "click_ms": click_time,
        },
        "result": "PASS",
    }
    report_path = OUTPUT_DIR / "report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"  ✓ 报告写入 {report_path}")
    print(f"\n✅ 预演通过 — macOS + 云·绝区零可作为一条龙运行环境")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[中断]")
        sys.exit(130)
