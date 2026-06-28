# 前端 macOS 适配 Task

本文档整理 macOS 平台上前端 GUI 的适配任务,作为后续 UX-A/B/C/D/E 系列在 mac 平台的延伸。
后端 win32 → macOS API 移植由其他 agent 负责,本文档只覆盖**前端 UX 层**。

---

## 1. 现状

仓库已有 `frontend_optimization_task.md` 完成 20 个跨平台 PR。
针对 mac,仍有以下 UX 层问题:

| # | 痛点 | 影响面 | 代码定位 |
|---|---|---|---|
| M1 | 启动按钮字体写死 `Microsoft YaHei`,mac 上无此字体 | 主页 | `gui/view/home/home_interface.py:400` |
| M2 | 应用图标写死 `logo.ico`,mac 不支持 ICO 格式 | 主窗口/安装器 | `gui/app.py:70`, `gui/zzz_installer_window.py:16` |
| M3 | 快捷键提示写死 `Ctrl+Enter`,mac 用户习惯 Cmd+Return | 主页按钮 | `gui/view/home/home_interface.py:404` |
| M4 | 画中画 Overlay 完全依赖 win32_utils,mac 启动失败但按钮仍显示 | 主页/独立应用 | `one_dragon_qt/overlay/overlay_manager.py`, `one_dragon_qt/widgets/pip_button.py` |
| M5 | 启动失败用 `ctypes.windll.user32.MessageBoxW` 弹窗,mac 无 windll | 启动异常处理 | `gui/app.py:254` |
| M6 | mac 期望菜单栏在顶部,目前应用内嵌 | 全局 | `one_dragon_qt/windows/window.py` |
| M7 | 关闭按钮行为:mac 习惯隐藏到 dock,目前是退出 | 主窗口 | `gui/app.py` closeEvent |
| M8 | `setQuitOnLastWindowClosed` 未设置,mac 上需要手动处理 | 主窗口 | qfluentwidgets 默认行为 |
| M9 | QFileDialog 风格:mac 应使用 sheet 风格而非 Qt 默认 | 资源下载/设置页 | qfluentwidgets 设置可能 |

---

## 2. 适配方向总览

| ID | 方向 | 优先级 | 工作量 | 风险 |
|---|---|---|---|---|
| MAC-A | 视觉一致性: 字体、图标、快捷键显示 | P0 | 小 | 低 |
| MAC-B | 平台降级: Overlay / windll 调用 | P1 | 中 | 低 |
| MAC-C | mac 系统集成: 菜单栏、关闭行为、Dock | P2 | 中 | 中 |

---

## 3. 详细任务

### MAC-A01 字体适配 [P0]

**现状**
`home_interface.py:400` 启动按钮字体写死 `QFont("Microsoft YaHei", 16, Bold)`。macOS 上没有 Microsoft YaHei,Qt 会 fallback 到系统字体(PingFang SC),导致按钮高度/宽度估算错误。

**方案**
- 在 `one_dragon_qt/utils/font_utils.py`(新建)提供 `get_ui_font(size, bold=False)` 函数
- 内部根据 `sys.platform` 选择字体:
  - `win32`: `Microsoft YaHei`
  - `darwin`: `PingFang SC`
  - `linux`: `Noto Sans CJK SC` 或系统默认
- 全局替换现有 `QFont("Microsoft YaHei", ...)` 为 `get_ui_font(...)`

**验收**
- mac 上启动按钮显示中文正确(无方块乱码)
- Windows 行为不变
- `home_interface.py` 不再有写死的 `Microsoft YaHei`

**涉及**
- 新建 `src/one_dragon_qt/utils/font_utils.py` (~30 行)
- `src/zzz_od/gui/view/home/home_interface.py`
- 其他用到 `Microsoft YaHei` 的位置

---

### MAC-A02 应用图标路径适配 [P0]

**现状**
`app.py:70` 使用 `app_icon='logo.ico'`。macOS 不支持 ICO 格式,需要 PNG 或 ICNS。

**方案**
- 优先使用 `'logo.png'`(跨平台),fallback 到 `logo.ico`(Windows only)
- 实际改动:在 `app.py` 与 `installer.py` 中根据 `sys.platform` 选择图标路径
- 不增加新资源文件(假设 `logo.png` 已存在于资源目录)

**验收**
- mac 上应用窗口左上角 / Dock 显示正确图标
- Windows 仍使用 `logo.ico`
- 没有 PNG 时 fallback 到 ICO 不报错

**涉及**
- `src/zzz_od/gui/app.py`
- `src/zzz_od/gui/zzz_installer_window.py`

---

### MAC-A03 快捷键显示适配 [P0]

**现状**
`home_interface.py:404` tooltip 写死 `"启动一条龙 (Ctrl+Enter)"`,实际绑定 `QKeySequence('Ctrl+Return')`。macOS 用户期望 `Cmd+Return`。

**方案**
- 使用 `QKeySequence.StandardKey` 或 `QKeySequence(QKeySequence.StandardKey.Save)` 等语义化常量
- mac 上 `QKeySequence('Ctrl+Return')` 自动转换为 `Cmd+Return` 显示
- tooltip 用 `button.shortcut().toString()` 自动获取平台对应的显示文案

**验收**
- mac 上 tooltip 显示 `⌘+Return` 或 `Meta+Return`
- Windows 仍显示 `Ctrl+Enter`
- 实际触发键正确(mac 按 ⌘+Return 触发)

**涉及**
- `src/zzz_od/gui/view/home/home_interface.py`

---

### MAC-B01 画中画 Overlay 在 mac 上降级 [P1]

**现状**
`overlay_manager.py` 完全依赖 `win32_utils`(已在 PR6 加 platform guard)。mac 上 OverlayManager 创建后会立即失败 / 无功能。`pip_button.py` 仍显示 PIP 按钮,点击行为不明。

**方案**
- `OverlayManager.create(ctx, parent)` 在 mac 上返回 None 或一个 NoOp 实例
- `PipButton` 在 `OverlayManager.instance()` 为 None 时,按钮 disabled 且 tooltip 提示"mac 暂不支持"
- mac 用户完全隐藏 PIP 按钮作为可选增强

**验收**
- mac 上点击 PIP 按钮不报错
- PIP 按钮显示 disabled 状态
- Windows 行为不变

**涉及**
- `src/one_dragon_qt/overlay/overlay_manager.py`
- `src/one_dragon_qt/widgets/pip_button.py` (or related)

---

### MAC-B02 启动失败错误弹窗 platform guard [P1]

**现状**
`gui/app.py:254` `ctypes.windll.user32.MessageBoxW(...)` 在 PR6 加了 windll import guard,但 MessageBoxW 调用本身仍是 Windows API,mac 上调用会失败。

**方案**
- mac 上用 `QMessageBox.critical(None, "错误", error_message)` 替代
- 跨平台方案:抽 `show_error_dialog(title, message)` 工具函数,内部判断平台
- mac 上同时支持打开浏览器(已经通过 `webbrowser.open` 实现)

**验收**
- mac 上启动失败有原生弹窗提示
- Windows 行为不变(继续用 MessageBoxW)

**涉及**
- `src/zzz_od/gui/app.py`

---

### MAC-C01 mac 系统集成(可选)[P2]

**现状**
mac 应用期望:
- 顶部全局菜单栏(`QMenuBar` 集成到 macOS menu bar)
- 关闭按钮 = 隐藏到 Dock,不是退出
- Dock 右键菜单有"退出"
- `Cmd+Q` 退出

当前应用未做这些适配。

**方案**
- 关闭按钮事件:mac 上 hide() 而非 close()
- `QApplication.setQuitOnLastWindowClosed(False)` 在 mac 上
- 全局快捷键 `Cmd+Q` 退出
- 此任务工作量大,P2 可后续做

**验收**
- mac 上点击关闭按钮,应用从屏幕消失但仍在 Dock
- Dock 右键有"退出"菜单
- `Cmd+Q` 退出应用

**涉及**
- `src/zzz_od/gui/app.py`
- `src/one_dragon_qt/windows/window.py`

---

## 4. 实施顺序建议

### M1 — 基础视觉(本次范围)

并行启动多 subagent:
- Subagent A: MAC-A01 字体
- Subagent B: MAC-A02 图标
- Subagent C: MAC-A03 快捷键

### M2 — 平台降级(本次范围)

并行启动:
- Subagent D: MAC-B01 Overlay
- Subagent E: MAC-B02 错误弹窗

### M3 — 系统集成(后续)

MAC-C01 P2 优先级,后续 PR 推进。

---

## 5. 多 subagent 并行实施策略

### 5.1 预调研(单 subagent)

启动 1 个 explore subagent,完整调研:
- 所有 `QFont("Microsoft YaHei"...)` 出现位置
- 所有 `logo.ico` / `.ico` 出现位置
- 所有 `windll.user32.MessageBoxW` 出现位置
- OverlayManager 在 mac 上的具体失败点
- `qfluentwidgets` 在 mac 上的默认菜单栏行为

输出:**精确的代码:行号清单**,供后续 subagent 直接编辑。

### 5.2 并行实施

基于调研结果,同时启动 5 个 general subagent:
- 每个 subagent 负责 1 个 task(上述 MAC-A01~MAC-B02)
- 每个 subagent 独立分支、独立 PR
- subagent 之间不共享修改文件(根据调研清单分配)

### 5.3 冲突避免规则

- 每个 subagent 限定修改文件范围
- 调研阶段确认各任务的文件不重叠
- 冲突时优先合并:打开 PR 后 reviewer 介入

---

## 6. 通用约定

- 改动优先 `if sys.platform == 'win32':` 守卫,不删除 Windows 路径
- 复用现有 `win32_utils.is_windows_build_supported` 等辅助函数
- 跨平台默认值优先选择 macOS,其次 Linux,最后 Windows(Windows 已经是多数 PR 的 baseline)
- 文档同步更新 `docs/develop/README.md` 的 mac 开发小节

---

## 7. 开放问题

1. **MAC-B01 Overlay 降级策略**:mac 上完全隐藏 vs 显示 disabled?
   - 建议:显示 disabled,保留未来扩展
2. **MAC-A02 图标资源**:logo.png 是否已经存在?
   - 需 subagent 调研确认
3. **MAC-C01 关闭行为**:mac 用户习惯差异大,是否提供"mac 模式"开关?
   - 建议:硬编码 mac 行为,符合平台惯例

---

## 8. 与已有 PR 的关系

- 与 PR6 (win32 import guard) 互补,处理 GUI 层遗留点
- 与 PR16 (MockController) 配合,让 mac 启动后 UI 也正常显示
- 不依赖任何未合并的 PR(全部基于 main)
