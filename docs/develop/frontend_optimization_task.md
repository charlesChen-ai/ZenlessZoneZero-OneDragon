# 前端展示与用户交互优化 Task

本文档整理当前 GUI 存在的可优化点,给出系统性的任务拆分与实施建议,供后续排期与迭代参考。
代码定位基于当前仓库 `src/`。

---

## 1. 现状分析

### 1.1 整体布局

```
MainAppWindowBase (FluentWindow)
├── NavigationInterface (左侧导航)
│   ├── 上方: 主页 / 游戏助手 / 一条龙 / 应用运行
│   └── 下方: 点赞 / 开发工具 / 代码同步 / 多账号 / 设置
└── StackedWidget (主内容区)
    ├── HomeInterface          仪表盘 (Banner + 启动按钮)
    ├── GameAssistantInterface Pivot: 战斗助手 / 委托助手
    ├── ZOneDragonInterface    Pivot: 运行 / 体力 / 预备编队 / 鼠标灵敏度
    ├── ZStandaloneAppInterface Pivot: 各独立应用
    └── ... 其它底部入口
```

每个 Pivot 页面常用 `SplitAppRunInterface`,应用运行页内嵌 `PageStackWrapper` 从右滑入二级设置页。

### 1.2 已识别痛点 (汇总)

| # | 痛点 | 影响面 | 代码定位 |
|---|---|---|---|
| P1 | 应用卡片单行塞 4 个动作 + 拖拽手柄,密度过高 | 一条龙 / 独立应用 | `widgets/setting_card/app_run_card.py:73` |
| P2 | `SettingCardBase` 固定 50px 高,内容最大 500px 强制省略 | 全部设置页 | `widgets/setting_card/setting_card_base.py:24,41` |
| P3 | 通知设置入口分散: 卡片"更多"菜单 + 一条龙顶部通知卡 | 一条龙运行 | `widgets/setting_card/app_run_card.py:54`, `view/one_dragon/one_dragon_run_interface.py:83` |
| P4 | 应用设置三层嵌套: 导航 → Pivot → 齿轮 → 滑入页 | 应用设置 | `widgets/pivot_navi_interface.py:99`, `docs/develop/guides/application_setting_guide.md` |
| P5 | "启动一条龙"按钮只跳转不启动,链路割裂 | 主页 | `gui/view/home/home_interface.py:655` |
| P6 | 嵌套滚动: StackedWidget → VerticalScroll → SingleDirectionScroll → DraggableList | 全部滚动页 | `widgets/vertical_scroll_interface.py:63`, `view/app_run_interface.py:241` |
| P7 | 主题色随 Banner 主色动态变,对比度不稳定 | 主页 | `gui/view/home/home_interface.py:744` |
| P8 | SwitchButton 语义含糊: 没 tooltip 说明"是否纳入一条龙" | 一条龙应用开关 | `view/one_dragon/one_dragon_run_interface.py:217` |
| P9 | 启动前 PreFlight 检查弹窗,缺失项跳转后无法一键回到原页 | 主页 → 设置 | `gui/view/home/home_interface.py:659` |
| P10 | Pivot 切换无动画/无状态保留,频繁切换丢失滚动位置 | 全部 Pivot 页 | `widgets/pivot_navi_interface.py` |

---

## 2. 优化方向总览

| ID | 方向 | 优先级 | 工作量 | 风险 |
|---|---|---|---|---|
| UX-A | 信息架构重组: 入口聚合 / 路径缩短 | P0 | 大 | 中 |
| UX-B | 视觉与可读性: 卡片高度 / 文字截断 / 主题 | P1 | 中 | 低 |
| UX-C | 操作路径优化: 启动链路 / 设置发现 / 一键回退 | P0 | 中 | 低 |
| UX-D | 交互反馈: 加载态 / 操作反馈 / 错误兜底 | P1 | 中 | 低 |
| UX-E | 跨平台与无障碍: mac 适配 / 键盘可达 / 高对比 | P2 | 中 | 低 |

---

## 3. 详细任务

### UX-A 信息架构重组

#### UX-A01 应用卡片动作区瘦身 [P1]

**现状**
`AppRunCard` 单卡 4 个按钮: 齿轮 / 三点菜单 / 运行 / SwitchButton,加上图标和拖拽手柄,50px 行高严重拥挤。
```
src/one_dragon_qt/widgets/setting_card/app_run_card.py:73
```

**方案**
- 把"移到顶部 / 通知设置"从三点菜单挪出,合并到"应用设置"Flyout 内部
- 运行按钮保留在最右侧,SwitchButton 紧邻运行按钮
- 齿轮按钮在未注册 AppSettingProvider 时隐藏 (`app_setting_manager.settable_app_ids` 已支持,见 `view/one_dragon/one_dragon_run_interface.py:284`)

**验收**
- 单卡可见按钮 ≤ 3 个 (齿轮 / 运行 / 开关)
- 卡片高度仍 50px,视觉不挤
- 通知设置入口统一收敛到齿轮 Flyout

**涉及**
- `widgets/setting_card/app_run_card.py`
- `widgets/app_setting/app_setting_flyout.py`
- `widgets/app_setting/app_notify_setting_flyout.py`

---

#### UX-A02 一条龙顶部"应用通知"卡片与全局通知设置入口合并 [P2]

**现状**
通知相关入口有 3 处:
- 应用卡片"更多 → 通知设置" (`app_run_card.py:54`)
- 一条龙顶部"应用通知"卡片 (`one_dragon_run_interface.py:83`)
- 设置 → 通知设置 (`view/setting/setting_push_interface.py`)

**方案**
- 顶部"应用通知"卡片只保留"启用通知总开关",移除冗余的"设置"按钮
- 单应用通知配置统一在齿轮 Flyout 内
- 全局推送通道 (SMTP / Webhook / ...) 保留在"设置 → 通知设置"

**验收**
- 用户配置"通知"路径 ≤ 2 步 (齿轮 Flyout 或 设置 → 通知)

**涉及**
- `view/one_dragon/one_dragon_run_interface.py`
- `widgets/app_setting/app_notify_setting_flyout.py`

---

#### UX-A03 应用设置层级收敛: 齿轮改用 FLYOUT 而非 INTERFACE [P0]

**现状**
当前应用设置推荐 `SettingType.INTERFACE`,需要:
1. 导航到一条龙 → Pivot 切到"运行"
2. 点击齿轮 → `push_setting_interface` 从右滑入新页
3. 顶部出现返回按钮,需手动点击返回

参考文档: `docs/develop/guides/application_setting_guide.md:14`

**方案**
- 优先推广 `SettingType.FLYOUT` (轻量弹窗),仅设置项 > 5 个时退回 INTERFACE
- Flyout 直接覆盖在卡片上,无需返回步骤
- Flyout 内部使用 Column + 现有 SettingCard,不做新组件

**验收**
- 默认 Provider 改用 FLYOUT (除已存在 INTERFACE Provider)
- 新建应用设置时,文档明确推荐 FLYOUT 优先

**涉及**
- `docs/develop/guides/application_setting_guide.md` (优先 INTERFACE → 优先 FLYOUT)
- 存量 INTERFACE Provider 不强制迁移,但 Flyout 基类可复用

---

### UX-B 视觉与可读性

#### UX-B01 SettingCardBase 高度自适应 + 取消 500px 强截断 [P1]

**现状**
```python
# src/one_dragon_qt/widgets/setting_card/setting_card_base.py
self.setFixedHeight(50)                       # 固定高度
self.contentLabel.setMaximumWidth(500)        # 内容最大 500px
```
长描述文本被强制省略,卡片宽时浪费空间。

**方案**
- 高度从 `fixed 50` 改为 `minimum 50`,内容超过时自适应
- 取消 `setMaximumWidth(500)`,改用 `setWordWrap(True)` 换行
- titleLabel 也允许换行,但默认 ellipsis 防止极端情况

**验收**
- 长描述在卡片内能完整显示或换行省略
- 单行卡片高度仍接近 50px (无回归)
- 已有 50px 假设的布局 (`setting_card_base.py:24`) 不被破坏

**涉及**
- `widgets/setting_card/setting_card_base.py`
- `widgets/setting_card/multi_push_setting_card.py` (高度 = 60 + 30 * 行)
- 全部使用 `SettingCardBase` 的子类

**风险**
- 自适应高度后 `SettingCardGroup` 内卡片间距需要确认仍合理

---

#### UX-B02 应用卡片支持富信息: 上次运行 / 状态 / 时长 [P2]

**现状**
`AppRunCard.update_display` 只显示"上次运行 yyyy-mm-dd HH:MM:SS",状态靠图标。
```python
# src/one_dragon_qt/widgets/setting_card/app_run_card.py:89
self.content_widget.setContent(f"{gt('上次运行')} {self.run_record.run_time}")
```

**方案**
- 内容区改为多行: 标题 + 副标题 (上次运行时间) + 状态徽章
- 状态徽章: 成功 (绿) / 失败 (红) / 运行中 (蓝) / 未运行 (灰)
- 失败时显示错误摘要 (新增 `AppRunRecord.error_message`)

**验收**
- 单卡不增加按钮,但信息密度提升
- 失败状态有红点 + tooltip,鼠标悬停看错误摘要

**涉及**
- `widgets/setting_card/app_run_card.py`
- `one_dragon/base/operation/application_run_record.py` (新增 error_message 字段)
- 数据库迁移: 旧记录 `error_message` 默认空字符串

---

#### UX-B03 主题色稳定性: Banner 主色提取增加对比度阈值 [P2]

**现状**
```python
# src/zzz_od/gui/view/home/home_interface.py:744
def _update_start_button_style_from_banner(self):
    theme_color = self._get_theme_color()
    foreground = get_foreground_color(r, g, b)
```
当 Banner 主色为深色时,启动按钮颜色也深,与背景区分度下降。

**方案**
- 计算主题色与 Banner 主色的对比度,低于阈值 (例如 3.0) 时切换到 Fluent 默认主题色
- 增加"始终使用 Fluent 默认主题色"开关,放在"设置 → 自定义"

**验收**
- 启动按钮在任意 Banner 下都能看清
- 开关开启时主题色固定,不随背景变

**涉及**
- `gui/view/home/home_interface.py`
- `view/setting/setting_custom_interface.py`
- `one_dragon_qt/services/theme_manager.py`

---

### UX-C 操作路径优化

#### UX-C01 主页"启动一条龙"真正启动,不再仅跳转 [P0]

**现状**
```python
# src/zzz_od/gui/view/home/home_interface.py:655
def _on_start_game(self):
    self._refresh_ready_state()
    issues = check_pre_flight(self.ctx)
    if issues:
        # 弹窗 → 跳转 → 设置 → 用户手动回主页
        ...
    self.ctx.signal.start_onedragon = True
    target = self._find_widget_by_name('one_dragon_interface')
    if target is not None:
        self.main_window.switchTo(target)
```
只是设了 `start_onedragon=True`,真正的启动在一条龙页面才发生。

**方案**
- PreFlight 通过后,直接调用 `OneDragonRunInterface.run_all_apps_signal.emit()` (已存在)
- PreFlight 不通过时,弹窗说明缺失项 + "去修复" 按钮,修复完成后自动回到主页,无需用户操作
- 修复流程: 跳转 → 设置 → 监听配置变化 → 校验通过 → 回到主页 → 自动重试启动

**验收**
- 配置正确时,主页按钮一键启动,无中间跳转
- 配置缺失时,自动修复完成后回到主页自动重试

**涉及**
- `gui/view/home/home_interface.py`
- `one_dragon_qt/view/one_dragon/one_dragon_run_interface.py` (run_all_apps_signal)
- 新增 `PreFlightCheckDialog` 自动重试逻辑

---

#### UX-C02 Pivot 切换状态保留 [P1]

**现状**
`PivotNavigatorInterface` 每次切换会 `currentChanged`,但 `stacked_widget` 实际是 `QStackedWidget`,widget 一直在,只是 hidden/shown。
```python
# src/one_dragon_qt/widgets/pivot_navi_interface.py:67
def on_current_index_changed(self, index: int):
    ...
    current_widget.on_interface_shown()
```
但滚动位置、临时选中状态可能被 `on_interface_hidden` 重置。

**方案**
- `BaseInterface` 增加 `save_state()` / `restore_state()` 钩子
- Pivot 切换时调用 `save_state`,回来时 `restore_state`
- 默认实现: 记录内部 `QScrollArea.verticalScrollBar().value()`

**验收**
- Pivot 标签来回切换,滚动位置不丢
- 应用选中状态不丢 (StandaloneRunInterface)

**涉及**
- `widgets/base_interface.py`
- `widgets/vertical_scroll_interface.py`
- `view/standalone_app_run_interface.py` (app_list 选中状态)

---

#### UX-C03 应用卡片开关加 tooltip 说明语义 [P1] ✅ 已完成 (2026-06-28)

**现状**
`SwitchButton` 在 `AppRunCard` 里控的是"是否纳入一条龙运行",但视觉上看不出。
```python
# src/one_dragon_qt/view/one_dragon/one_dragon_run_interface.py:210
def on_app_switch_run(self, app_id: str, value: bool):
    self.config.set_app_enable(app_id, value)
```

**方案 (已实施,最小改动版)**
为降低风险,本次未引入新图标或新组件,改为在 SwitchButton 上直接 `setToolTip`:
- `AppRunCard.switch_btn`: 直接设置硬编码中文 tooltip
- `SwitchSettingCard`: 新增可选参数 `tooltip_cn: str | None = None`,默认 None 时不加 tooltip (零侵入,既有调用方不受影响)
- `PasswordSwitchSettingCard`: 本次范围外,后续按需扩展

**实际改动**
- `src/one_dragon_qt/widgets/setting_card/app_run_card.py:70` 新增 1 行 tooltip
- `src/one_dragon_qt/widgets/setting_card/switch_setting_card.py:25,50-51` 新增可选参数与守卫

**验收**
- ✅ hover 一条龙运行页任一应用卡片右侧的开关,显示"关闭后此应用不会在一键启动一条龙中运行,仍可在独立应用页运行"
- ✅ 既有 `SwitchSettingCard` 调用方零修改,行为不变
- ✅ 后续需要时,业务侧可在 `SwitchSettingCard(..., tooltip_cn='...')` 中按需启用
- ✅ ruff check: 本次改动未引入新错误 (6 个既有遗留问题与本次无关)

**未完成项 / 后续**
- titleLabel 旁加 info 图标的方案未实施 (会改动 `SettingCardBase` 布局,牵连所有 SettingCard,风险较大)
- `PasswordSwitchSettingCard` 未同步 (本次最小改动原则)

**涉及**
- `widgets/setting_card/switch_setting_card.py` ✅
- `widgets/setting_card/app_run_card.py` ✅
- `widgets/setting_card/setting_card_base.py` (未动,延后)
- `widgets/setting_card/password_switch_setting_card.py` (未动,延后)

---

### UX-D 交互反馈

#### UX-D01 异步操作加载态统一 [P1]

**现状**
各页面"开始运行"按钮点击后,只更新文字为"运行中"。后台配置加载 (例如 `ctx.init()`) 期间,部分界面可能短暂空白或状态错。

**方案**
- 引入 `LoadingOverlay` 组件,半透明遮罩 + Fluent ProgressRing + 文案
- 关键入口 (首页启动、设置初始化、模型下载) 套用此组件
- 框架层提供 `with_loading(widget, task_fn)` 装饰器,业务侧最少改动

**验收**
- `ctx.init()` 期间界面不闪烁
- 长时间操作 (>500ms) 有可见反馈

**涉及**
- `one_dragon_qt/widgets/loading_overlay.py` (新增)
- `gui/app.py:50` (主窗口初始化)
- `gui/view/home/home_interface.py` (启动流程)

---

#### UX-D02 操作失败统一 InfoBar + 重试入口 [P2]

**现状**
`log.error` 在控制台输出,GUI 上无提示。`setting_push_interface.py:404` 有 `_show_error_message` 但仅本页面使用。

**方案**
- 引入 `notify_error(title, content, retry_fn=None)` 全局工具
- 关键操作 (启动 / 截图 / OCR 失败) 自动调用
- 带 `retry_fn` 时 InfoBar 显示"重试"按钮

**验收**
- 启动失败时,用户能看到红色 InfoBar + 重试按钮
- 不弹窗阻断,操作可继续

**涉及**
- `one_dragon_qt/utils/notify_utils.py` (新增)
- `gui/app.py` 已有 `context_notify_signal` 可复用

---

#### UX-D03 日志面板交互优化 [P2]

**现状**
`LogDisplayCard` 只展示滚动日志,无法搜索、复制、过滤。

**方案**
- 增加搜索框 (Ctrl+F),实时高亮
- 右键菜单: 复制选中行 / 复制全部 / 清屏
- 过滤级别 (INFO / WARNING / ERROR) 切换

**验收**
- 日志可搜索、可复制
- 过滤后不影响运行时实际日志级别

**涉及**
- `widgets/log_display_card.py`
- `one_dragon/utils/log_utils.py`

---

### UX-E 跨平台与无障碍

#### UX-E01 mac 开发适配: Stub Controller 接入 [P0]

**现状**
当前 `PcControllerBase` 顶层 `import win32api/gui/con/ui`,mac 上 import 链断裂,业务模块无法加载。

**方案**
详见会话中已讨论的"mac 开发工作流"。

**任务清单**
1. `pc_controller_base.py` / `pc_game_window.py` / `pc_clipboard.py` 顶层 win32 import 改 platform guard
2. `one_dragon/base/controller/` 下新增 `mock_controller.py` (继承 `ControllerBase`)
3. `OneDragonContext` 根据 `sys.platform` 选择 Controller
4. `pyproject.toml` 增加 `onnxruntime-cpu` 作为非 Windows 平台的依赖
5. mac 上 `uv run src/zzz_od/gui/app.py` 能起 GUI,业务模块可 import

**验收**
- mac 上 `python -c "import one_dragon.base.operation.one_dragon_context"` 不报错
- mac 上启动 GUI,主页 / 设置页可浏览,运行按钮点击有 mock 行为
- Windows 实机行为不变

**涉及**
- `src/one_dragon/base/controller/pc_controller_base.py`
- `src/one_dragon/base/controller/pc_game_window.py`
- `src/one_dragon/base/controller/pc_clipboard.py`
- `src/one_dragon/base/controller/mock_controller.py` (新增)
- `src/one_dragon/base/operation/one_dragon_context.py`
- `pyproject.toml`
- `docs/develop/README.md` (新增"mac 开发"小节)

---

#### UX-E02 键盘可达性: Tab 顺序 / 快捷键 [P2]

**现状**
未审计键盘 Tab 顺序。常用操作 (开始 / 停止 / 设置) 依赖鼠标。

**方案**
- 主页"启动一条龙"绑定 `Ctrl+Enter`
- 应用运行页"开始/停止"绑定 `Space` (已有 start/stop key,但 UI 未提示)
- 设置页 `Ctrl+S` 保存 (YAML 自动保存可省,但保留习惯)
- 所有按钮设置 `setShortcut()` + tooltip 显示快捷键

**验收**
- 主页可不使用鼠标完成"启动 → 停止"
- 关键按钮 hover 显示快捷键

**涉及**
- `gui/view/home/home_interface.py`
- `view/app_run_interface.py`

---

#### UX-E03 高对比度模式适配 [P3]

**现状**
默认 Fluent Light / Dark 主题,无高对比度选项。

**方案**
- 设置页增加"高对比度"开关
- 开启后使用 Fluent 高对比度配色 (qfluentwidgets 已支持),并加大字体

**验收**
- 系统级高对比度模式下,GUI 元素对比度 ≥ 7:1

**涉及**
- `view/setting/setting_custom_interface.py`
- `one_dragon_qt/services/theme_manager.py`

---

## 4. 实施顺序建议

### 4.1 依赖关系

```
UX-E01 (mac 适配)
   └── 后续 mac 上验证所有改动的前提
   
UX-C03 (开关 tooltip)        ─┐
UX-A03 (FLYOUT 优先)         ─┤── 依赖 UX-E01 后可在 mac 上验证
UX-A01 (卡片瘦身)            ─┘
   
UX-B01 (卡片高度自适应)       ─┐
UX-D01 (加载态)              ─┤── 跨多个页面,需先收敛 SettingCard
UX-C02 (Pivot 状态保留)      ─┘
   
UX-C01 (启动一键化)           ── 依赖 UX-A03 (FLYOUT) 收敛后路径更顺
   
UX-A02 (通知入口合并)        ── 依赖 UX-A01 卡片瘦身
UX-B02 (应用卡片富信息)       ── 依赖 UX-A01 卡片瘦身
UX-B03 (主题色对比度)        ── 独立
UX-D02 (操作失败 InfoBar)    ── 依赖 UX-D01 加载态基础组件
UX-D03 (日志面板)            ── 独立
UX-E02 (键盘可达)            ── 独立
UX-E03 (高对比度)            ── 独立
```

### 4.2 里程碑建议

**M1 - 跨平台开发基础 (1-2 周)**
- UX-E01 mac 适配
- 文档: mac 开发指南

**M2 - 核心交互收敛 (2-3 周)**
- UX-A01 卡片瘦身
- UX-A03 FLYOUT 优先
- UX-C01 启动一键化
- UX-C03 开关 tooltip

**M3 - 视觉与反馈 (2 周)**
- UX-B01 卡片自适应
- UX-D01 加载态
- UX-C02 Pivot 状态保留

**M4 - 体验打磨 (持续)**
- UX-A02 通知入口合并
- UX-B02 应用卡片富信息
- UX-B03 主题色对比度
- UX-D02 操作失败 InfoBar
- UX-D03 日志面板
- UX-E02 键盘可达
- UX-E03 高对比度

---

## 5. 通用约定

- 改动需同步更新 `docs/develop/` 下的对应文档
- 涉及 UI 改动时,在 PR 描述附截图 / 录屏
- 新增交互组件必须有 `AdapterInitMixin` 支持 (若涉及配置)
- 跨平台改动 (UX-E01) 必须在 Windows 实机回归
- 参考现有组件复用,避免新增平行实现

---

## 6. 开放问题

1. UX-A03 是否要强制迁移存量 INTERFACE Provider?建议保留,只对新 Provider 默认 FLYOUT
2. UX-B02 是否需要新增数据库迁移脚本?建议加,旧记录 error_message 默认空
3. UX-C01 自动重试机制是否要可关闭?建议默认开启,设置页提供总开关
4. UX-E01 mac 上 `uv run app.py` 启动后,主页 Banner 是否能加载?需在 PR 后验证
