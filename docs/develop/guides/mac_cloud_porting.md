# macOS + 云游戏 移植任务文档

> 目标：把 `ZenlessZoneZero-OneDragon` 改造成可在 **macOS** 上运行、操作一台本地 **云游戏客户端窗口**（如云·绝区零、网易云游戏、腾讯 START 云游戏、BOOYAH 等任意 H.264/HEVC 流到本地的窗口）完成一条龙。
>
> 范围限定：仅前台模式（**禁用**后台 PostMessage / `vgamepad` 虚拟手柄），接受云游戏带来的网络延迟与画面差异。

## 0. 现状摘要（已勘探）

### 0.1 Windows 硬绑定盘点

源码层（按子系统归类）：

| 子系统 | 代表文件 | 关键 API |
|---|---|---|
| 游戏窗口 | `src/one_dragon/base/controller/pc_game_window.py` | `ctypes.windll.user32.GetClientRect` / `ClientToScreen` / `IsWindow` / `IsIconic` / `ShowWindow`；`pygetwindow.Win32Window` |
| 截图 | `src/one_dragon/base/controller/pc_screenshot/{print_window,bitblt,gdi_*,pil}_screencapper.py` | `gdi32.BitBlt` / `user32.PrintWindow` / `user32.GetDC` / `gdi32.CreateDIBSection` / `gdi32.CreateCompatibleDC` / `PIL.ImageGrab` |
| 键鼠 - 前台 | `src/one_dragon/base/controller/pc_controller_base.py:293-319` | `pyautogui` / `pynput.keyboard`（**跨平台**） |
| 键鼠 - 后台 | `src/one_dragon/base/controller/pc_controller_base.py:355-396,460-487` | `win32gui.PostMessage(WM_LBUTTONDOWN/UP)` / `WM_ACTIVATE(WA_ACTIVE)` / `mouse_event` |
| 手柄 - 后台 | `pc_controller_base.py:104-119,233-245`；`src/one_dragon/base/controller/pc_button/{xbox,ds4}_button_controller.py` | `vgamepad`（ViGEm，Windows-only 驱动） |
| 鼠标 Raw Input 闪切 | `pc_controller_base.py:200-231` | `user32.mouse_event(0x0001, ...)` 触发游戏 Raw Input |
| 剪贴板 | `src/one_dragon/base/controller/pc_clipboard.py`；`src/one_dragon/utils/debug_utils.py:35-53` | `win32clipboard.SetClipboardData(CF_DIB/CF_UNICODETEXT)` / `pywintypes` |
| Overlay | `src/one_dragon_qt/overlay/utils/win32_utils.py`；`overlay_manager.py:499,501,573,582,860,879`；`overlay_window.py:138,143` | `user32.SetWindowLongW(WS_EX_LAYERED/WS_EX_TRANSPARENT)` / `SetWindowDisplayAffinity(WDA_EXCLUDEFROMCAPTURE)` / `GetAsyncKeyState` |
| 错误弹窗 | `src/zzz_od/gui/app.py:254`；`src/one_dragon/launcher/runtime_launcher.py:85-97`；`src/zzz_od/win_exe/runtime_launcher.py:11` | `user32.MessageBoxW` |
| 启动器 / 进程管理 | `src/one_dragon/devtools/python_launcher.py:158-260` | `kernel32.CreateJobObjectW` + `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` |
| 启动参数解析 | `src/one_dragon/devtools/python_launcher.py:158` | `os.name == 'nt'` 分支；隐藏控制台 |
| ONNX | `src/one_dragon/yolo/onnx_model_loader.py:130-146`；`src/onnxocr/predict_base.py:10-25`；`src/one_dragon/utils/gpu_executor.py` | `DmlExecutionProvider`（DirectML，Windows-only） |
| 音频（闪避） | `src/zzz_od/auto_battle/auto_battle_dodge_context.py:84-110` | `soundcard.mediafoundation.SoundcardRuntimeWarning`（Windows Media Foundation 桥）；`sc.get_microphone(include_loopback=True)` 取系统回放 |
| 找窗口 | `pc_game_window.py:38` | `pyautogui.getWindowsWithTitle` → 内部用 `pygetwindow`（Win32） |
| 路径 | `src/one_dragon_qt/view/setting/setting_custom_interface.py:159` | `shell32.SHGetFolderPathW` 选"我的文档"作为 banner 默认路径 |
| 屏幕缩放 / DPI | `one_dragon_qt/overlay/utils/win32_utils.py:86-100` | `shcore.GetProcessDpiAwareness` |

依赖层：

| 依赖 | 平台 | 影响 |
|---|---|---|
| `onnxruntime-directml==1.18.0` | Windows only | 推理后端需要换 |
| `pywin32`（隐式） | Windows only | 剪贴板、JobObject、MessageBox 全部依赖 |
| `pygetwindow` | 默认 Windows 后端 | `getWindowsWithTitle` 行为依赖 |
| `vgamepad`（`gamepad` extra） | Windows + ViGEm 驱动 | 后台手柄模式不可用 |
| `soundcard==0.4.3` | 跨平台但 CoreAudio 上有 bug | 音频闪避需换实现 |
| `pyuac`（dev） | Windows only | 提权，仅 dev 工具需要 |
| `pygit2` | 跨平台但需 libgit2 | brew 装一下即可 |

打包层（`pyproject.toml:42`）：
```toml
[tool.uv]
environments = ["sys_platform == 'win32'"]
```
uv 在 macOS 上**直接拒绝解析**，是头号路障。

### 0.2 云游戏兼容性

| 维度 | 可行性 | 备注 |
|---|---|---|
| 找窗口 | ✅ | 客户端是本地窗口，已有 `custom_win_title` 设置项可填 |
| 截图 | ✅ | 用 `mss` 抓矩形，`mss` 跨平台 |
| 物理键鼠 | ✅ | `pyautogui` / `pynput` 跨平台，事件会被云客户端转发 |
| 后台 PostMessage | ❌ | 消息只到客户端进程，云端游戏收不到 |
| 虚拟手柄 | ❌ | macOS 无 ViGEm，云端是否支持手柄看具体厂商 |
| 鼠标 Raw Input 闪切 | ⚠️ | 取决于云客户端是否透传 Raw Input；多数不行 |
| 音频回采闪避 | ⚠️ | 需要本地装 BlackHole 等虚拟音频设备 |
| 时序敏感操作（闪避/连携） | ⚠️ | 网络延迟 30–100ms，硬编码时序基本失效 |
| 1080p 坐标 | ⚠️ | 需要云客户端窗口固定 1920x1080 client rect |
| HDR / 显示器序号 / 全屏启动 | ❌ | 都是控制本地游戏客户端的参数，对云游戏无意义 |

## 1. 目标架构

### 1.1 设计原则
- **优先抽出 platform layer**（窗口 / 输入 / 截图 / 剪贴板 / 弹窗 / Overlay / Hotkey），不写 `if sys.platform == 'win32': ...` 散落到业务里。
- **降级而不是补齐**：macOS 上不试图复刻后台 PostMessage 模式，**直接关掉**。
- **可观测性优先**：云游戏延迟高，调试日志和帧缓存（已有 `.debug/images/`）必须在 macOS 一样工作。

### 1.2 推荐分层

新增目录：
```
src/one_dragon/platform/
├── __init__.py
├── window_service.py        # 平台无关的窗口抽象 + Windows/macOS 实现
├── input_service.py         # 平台无关的键鼠抽象
├── screenshot_service.py    # 把 4 种策略改为注册式，加 macOS-only 策略
├── clipboard_service.py     # 跨平台剪贴板
├── overlay_service.py       # 替代 win32_utils.py
├── hotkey_service.py        # 跨平台热键监听
├── dialog_service.py        # 替代 MessageBoxW
├── console_service.py       # 替代 kernel32 控制台隐藏/JobObject
└── _impl/
    ├── windows/             # 现有 Win32 实现搬过来
    └── macos/               # 新增：AppKit/Quartz 实现
```

迁移时**保留旧类名 + 文件路径**以减少业务侧改动（`PcGameWindow` / `PcControllerBase` / `PcScreenshotController` 仍然可 import），内部把对 win32 的直调替换为 `WindowService` / `InputService` / `ScreenshotService` 的调用。

### 1.3 输入模型选择

| 模式 | 原 Windows 行为 | macOS + 云游戏策略 |
|---|---|---|
| foreground | `pyautogui` + `pynput` | **直接保留**，无需改动 |
| background | PostMessage + 虚拟手柄 | **禁用**：在 macOS 上 `enable_background_mode` 写日志告警并强制回 foreground |
| mouse_flash（Raw Input 切换） | `user32.mouse_event` | **禁用** |

设置面板（`setting_game_interface.py:97-155`）：macOS 下隐藏整组"后台模式（测试版）"卡片（`isVisibleBasedOnPlatform()` 或按 `sys.platform` 在 `_get_content_widget` 里跳过）。

## 2. 任务拆分（按可独立验收的 Phase 顺序）

> 标签说明：`[P0]` 必须做才能跑起来；`[P1]` 影响体验但可分批；`[P2]` 收尾。
> 验收方式以"在 macOS 上能 import、能跑 GUI 窗口、能完成一条龙主流程一次"为最终目标。

### Phase 0：解锁平台限制（半天）

- [P0] `pyproject.toml:42` 去掉 `environments = ["sys_platform == 'win32']`，或改为 `["sys_platform == 'win32'", "sys_platform == 'darwin'"]`。
- [P0] `pyproject.toml:6-21` 拆出平台条件依赖：
  ```toml
  [project]
  dependencies = [
      "pyside6==6.8.0.2",
      "pyside6-fluent-widgets==1.11.1",
      "pyyaml==6.0.1",
      "opencv-python==4.10.0.84",
      "pyautogui==0.9.54",
      "pynput==1.7.7",
      "mss==9.0.1",
      "shapely==2.0.4",
      "pyclipper==1.3.0.post5",
      "librosa==0.10.2.post1",
      "gensim==4.3.3",
      "pygit2==1.19.0",
      "onnxruntime>=1.18.0",  # 取消 directml 锁定
  ]

  [dependency-groups]
  macos = [
      "pyobjc-framework-Cocoa>=10.0",
      "pyobjc-framework-Quartz>=10.0",
  ]
  win = [
      "pywin32>=306",
      "onnxruntime-directml==1.18.0",
  ]

  gamepad = [
      "vgamepad==0.1.0 ; sys_platform == 'win32'",
  ]
  ```
  并在 `tool.uv.environments` 写 `["sys_platform == 'win32'", "sys_platform == 'darwin'"]`。

- [P0] 处理 `pygit2`：macOS 上 `brew install libgit2` 后 uv 装 `pygit2` wheel 即可；`.env.sample.bat` 没有 macOS 对应物，新建 `.env.sample.sh`（仅 `PYTHONPATH=src`）。

**验收**：`uv sync` 在 macOS 上成功；`uv run python -c "import one_dragon, zzz_od"` 不抛 `ModuleNotFoundError`。

---

### Phase 1：平台抽象 - 窗口 / 截图（3–5 天）

#### 1.1 窗口抽象
- [P0] 新增 `src/one_dragon/platform/window_service.py`，定义：
  ```python
  class WindowService(ABC):
      def find_by_title(self, title: str) -> WindowInfo | None: ...
      def get_client_rect(self, info: WindowInfo) -> Rect | None: ...
      def client_to_screen(self, info: WindowInfo, x: int, y: int) -> tuple[int, int]: ...
      def is_window(self, info: WindowInfo) -> bool: ...
      def is_minimized(self, info: WindowInfo) -> bool: ...
      def show(self, info: WindowInfo, show_cmd: int) -> None: ...  # 替代 ShowWindow
      def activate(self, info: WindowInfo) -> None: ...
      def get_foreground(self) -> WindowInfo | None: ...  # 替代 GetForegroundWindow
  ```
- [P0] `_impl/windows/window_service.py`：把 `pc_game_window.py:79,94,170,179,185,192` 全部改走 `WindowService`，但保留 `PcGameWindow` 公共接口。
- [P0] `_impl/macos/window_service.py`：用 `Quartz.CGWindowListCopyWindowInfo` 找窗口；`Quartz.CGWindowGetBounds` 取 client rect；`AppKit.NSApp.activate(ignoringOtherApps_=True)` 激活；`Quartz.CGWindowListCopyWindowInfo` 配合 `kCGWindowLayer == 0` 判断前台。
- [P0] `pc_game_window.py:38` 的 `pyautogui.getWindowsWithTitle` 替换为 `WindowService.find_by_title`（`pyautogui` 在 macOS 上行为不可靠）。

**验收**：写一个 `tests/one_dragon/platform/test_window_service_macos.py`，能在 macOS 上拿到云游戏窗口的 client rect。

#### 1.2 截图抽象
- [P0] `pc_screenshot/pc_screenshot_controller.py:32-37` 改为按平台注册：
  ```python
  def __init__(self, ...):
      self.strategies = {}
      if sys.platform == 'win32':
          self.strategies[ScreenshotMethodEnum.PRINT_WINDOW.value.value] = PrintWindowScreencapper(...)
          self.strategies[ScreenshotMethodEnum.BITBLT.value.value] = BitBltScreencapper(...)
      self.strategies[ScreenshotMethodEnum.MSS.value.value] = MssScreencapper(...)
      self.strategies[ScreenshotMethodEnum.PIL.value.value] = PilScreencapper(...)
  ```
  默认优先级在 macOS 上自动变为 `[MSS, PIL]`。
- [P0] `env_config.py:70-76` 的 `ScreenshotMethodEnum` 新增 `MACOS_SCREENCAPTURE`（可选，用 `Quartz.CGWindowListCreateImage` 抓指定 window id，对 DComp/Metal 渲染兼容更好）。
- [P0] `setting_env_interface.py:64-69` 的截图方法下拉在 macOS 上只显示 MSS / PIL（用 `FilterProxyModel` 过滤，或干脆按平台构造不同 enum）。

**验收**：在 macOS 上打开云游戏窗口，运行一条龙截图功能，能稳定返回正确分辨率的 BGR/RGB 数组。

---

### Phase 2：平台抽象 - 输入（2–3 天）

- [P0] 新增 `src/one_dragon/platform/input_service.py`：
  ```python
  class InputService(ABC):
      def click(self, x: int, y: int, button: str = 'left', press_time: float = 0) -> None: ...
      def move_relative(self, dx: int, dy: int) -> None: ...  # 替代 mouse_event
      def key_tap(self, key: str) -> None: ...
      def key_press(self, key: str, press_time: float | None = None) -> None: ...
      def key_release(self, key: str) -> None: ...
      def scroll(self, dx: int, dy: int) -> None: ...
  ```
- [P0] `_impl/windows/input_service.py`：`pyautogui` + `pynput`（保留现有前台路径）。
- [P0] `_impl/macos/input_service.py`：`pyautogui` + `pynput`（同样跨平台）。**不需要**写 AppKit。
- [P0] `pc_controller_base.py:355-396,460-487` 的 `_background_click` / `_drag_to` 改为：
  ```python
  def _background_click(self, ...) -> bool:
      log.error('后台 PostMessage 模式在当前平台不可用，已自动忽略')
      return self._foreground_click(pos, press_time, pc_alt=False)
  ```
- [P0] `pc_controller_base.py:200-231` 的 `_ensure_mouse_mode` 改为在 macOS 上 noop + 日志（云端不感知 Raw Input）。
- [P0] `pc_controller_base.py:174-198` 的 `enable_background_mode`：检测到非 Windows 直接 `log.warning` 并回 `enable_foreground_mode()`。
- [P1] `setting_game_interface.py:97-155` 的后台模式整组卡片，在 macOS 上不渲染（`sys.platform != 'win32'` 时跳过 `_get_background_mode_group`）。

**验收**：在 macOS 上 `enable_background_mode()` 不抛异常；业务点击走 pyautogui；云游戏窗口收到点击并触发游戏内交互。

---

### Phase 3：平台抽象 - 杂项（剪贴板 / Overlay / Hotkey / 弹窗 / 启动器）（3–4 天）

- [P0] 剪贴板 `pc_clipboard.py`、`debug_utils.py:35-53`：
  - macOS 实现用 `AppKit.NSPasteboard.generalPasteboard()`。
  - 抽出 `platform/clipboard_service.py` 公共接口 `set_text / get_text / set_image / get_image`。
- [P0] Overlay `one_dragon_qt/overlay/utils/win32_utils.py`：
  - `is_key_pressed` / `is_ctrl_pressed` / `is_alt_pressed` → macOS 改用 `pynput.keyboard` 全局监听（`Listener` + 状态缓存）。
  - `set_window_click_through` → macOS 用 `NSWindow.setIgnoresMouseEvents_`。
  - `set_window_display_affinity` (WDA_EXCLUDEFROMCAPTURE) → macOS 上**没有等价**（私有 API `NSWindowSharingNone`），先 noop + 日志。
  - `is_window_minimized` / `is_window_visible` → 走 `Quartz`。
  - 抽到 `platform/overlay_service.py`，旧文件保留为 shim 或直接改 import。
- [P0] 错误弹窗 `gui/app.py:254`、`runtime_launcher.py:92`、`zzz_od/win_exe/runtime_launcher.py:11`：
  - macOS 用 `tkinter.messagebox.showerror`（stdlib 即可，避免再装一个 Qt 二次依赖），或直接 `QMessageBox.critical`（已经是 PySide6 进程里）。
  - 抽到 `platform/dialog_service.py`。
- [P0] 启动器 `src/one_dragon/devtools/python_launcher.py:158-260`：
  - `os.name == 'nt'` 分支包成 `_windows_job_object`；macOS 上不需要 JobObject，用 `subprocess.Popen` + 注册 `atexit` 清理即可。
  - 隐藏控制台 `_hide_console` 在 macOS 上 noop。
- [P1] `setting_custom_interface.py:159` 的 `shell32.SHGetFolderPathW` → `pathlib.Path.home() / 'Documents'`。
- [P1] `runtime_launcher.py:85` 的 `kernel32.GetConsoleWindow` → noop。

**验收**：在 macOS 上从命令行 `uv run src/zzz_od/gui/app.py` 能拉起 GUI；启动失败时弹出 QMessageBox 而不是 `ctypes.windll` 报错。

---

### Phase 4：推理后端与音频（2–3 天）

#### 4.1 ONNX
- [P0] `one_dragon/yolo/onnx_model_loader.py:130-146`：把 `DmlExecutionProvider` 选择逻辑改为按平台选：
  ```python
  if sys.platform == 'win32' and 'DmlExecutionProvider' in availables:
      providers = ['DmlExecutionProvider']
  elif sys.platform == 'darwin' and 'CoreMLExecutionProvider' in availables:
      providers = ['CoreMLExecutionProvider']
  else:
      providers = ['CPUExecutionProvider']
  ```
- [P0] `onnxocr/predict_base.py:10-25` 同步改。
- [P0] `one_dragon/utils/gpu_executor.py:11-44` 的 `_DML_PROVIDER` 常量改为按平台可配置；`should_serialize_providers` 在 macOS 上对 CoreML 也走串行（CoreML session 并发同样会崩）。
- [P1] 给 `model_config` 增加"推理后端"设置项，让用户在 Auto / CoreML / CPU 之间切。

**验收**：在 macOS 上加载 YOLO 闪避分类器 + OCR 模型不报 `DmlExecutionProvider not found`；OCR 一次截图耗时 < 1s（M2 Air 参考）。

#### 4.2 音频闪避
- [P0] `auto_battle_dodge_context.py:84-110` 的 `soundcard` 调用：
  - macOS 替换为 `sounddevice` + `BlackHole` 虚拟设备的输入。
  - 文档要求用户安装 `BlackHole 2ch` 并把它设为系统默认输出。
  - 实现层抽出 `platform/audio_loopback_service.py`：
    ```python
    class AudioLoopbackService(ABC):
        def list_loopback_devices(self) -> list[str]: ...
        def open_stream(self, device_name: str, samplerate: int, channels: int) -> AudioStream: ...
    ```
- [P1] 在设置里加"音频回采设备"下拉（用 `sounddevice.query_devices()` 列举）。
- [P2] 闪避设置加"云游戏模式：跳过音频闪避"开关（默认开），降低误报。

**验收**：在 macOS 上能跑通音频闪避一次（手动触发一段系统音，应能识别并闪避）。

---

### Phase 5：UI 与配置（1–2 天）

- [P0] `setting_game_interface.py:84-91` 的"启用/禁用 HDR"、"切换 HDR 状态"按钮：macOS 上隐藏（云游戏无 HDR 控制权）。
- [P0] `setting_game_interface.py:157-182` 的"启动参数"组（无边框窗口 / 全屏 / 显示器序号 / 高级参数）：macOS 上折叠为"本地启动参数（仅在直接启动绝区零时生效）"并标注云游戏场景下忽略。
- [P0] `setting_env_interface.py:64-69` 截图方法下拉在 macOS 上隐藏 Win32-only 项。
- [P0] `setting_instance_interface.py:308-316` 的"自定义窗口标题"在 macOS 上给默认值提示：建议填"云·绝区零" / "云游戏"等可能匹配的标题。
- [P1] `application/game_config_checker/mouse_sensitivity_checker/` 整体在 macOS 上隐藏入口（云游戏不可校准）。
- [P1] `gamepad_turn_speed`、`turn_dx` 在云游戏模式下意义有限，文档化"建议保持默认"。

**验收**：在 macOS 上首次启动一条龙，看到的设置项没有"后台模式 / HDR / 启动参数"等不适用的卡片。

---

### Phase 6：启动 / 打包 / 文档（1–2 天）

- [P0] `src/zzz_od/win_exe/runtime_launcher.py` 改名 `runtime_launcher.py` 移到 `src/zzz_od/launcher/`，去掉 win32 调用；`deploy/` 下的 `.spec` 文件拆出 macOS 版（`OneDragon-Launcher-macOS.spec`）。
- [P1] `debug.bat` 改写为 `scripts/run_dev.sh`（macOS / Linux 通吃）。
- [P1] 新增 `scripts/install_macos_brew_deps.sh`（libgit2、BlackHole 提示）。
- [P0] 新增 `docs/develop/guides/mac_cloud_porting.md`（**就是本文档**）。
- [P1] `docs/develop/one_dragon/one_dragon_architecture.md` 增加"平台抽象"小节。
- [P1] `AGENTS.md` 顶部"深入阅读"区域增加本文档链接。
- [P1] `README.md` 增加"macOS + 云游戏（实验性）"段落。

**验收**：`uv run src/zzz_od/gui/app.py` 在 macOS 上从空环境（仅装了 brew 依赖）能完整跑起来。

---

### Phase 7：测试（贯穿）

- [P0] `tests/one_dragon/platform/test_window_service.py`：mock + 真实两组，至少覆盖 find_by_title / client_to_screen。
- [P0] `tests/one_dragon/platform/test_screenshot_service.py`：在 macOS 上用 `Quartz.CGWindowListCreateImage` 截自己的 Qt 窗口验证。
- [P0] `tests/one_dragon/platform/test_input_service.py`：mock 模式验证 click 走 pyautogui。
- [P1] `zzz-od-test/`：在 macOS 上跑通至少一个 screenshot-based 的回归用例（吃面 / 传送 等非战斗场景）。
- [P2] E2E：在 macOS + 云游戏上跑通一条龙全流程，记录日志到 `docs/develop/zzz/cloud_e2e_report.md`。

**验收**：`uv run pytest tests/one_dragon/platform/` 全绿；`zzz-od-test/` 在 macOS 上至少 5 个用例过。

## 3. 已知不可行 / 不在范围

| 项 | 原因 | 处理 |
|---|---|---|
| 后台 PostMessage 模式 | macOS 没有等价；云游戏也不需要 | 直接禁用，UI 隐藏 |
| vgamepad 虚拟手柄 | macOS 无 ViGEm 驱动 | `gamepad` extra 改为 Windows-only；UI 隐藏 |
| 云游戏下音频闪避 | 需要装 BlackHole，且受码率影响 | 实现但默认关，提供开关 |
| 云游戏下闪避 / 连携 | 30–100ms 延迟下时序失效 | 文档说明，不承诺自动化质量 |
| 云游戏下鼠标灵敏度校准 | 灵敏度不可控 | 工具入口隐藏 |
| HDR / 显示器 / 全屏参数 | 不控制本地游戏进程 | UI 隐藏 |
| WDA_EXCLUDEFROMCAPTURE | macOS 无公开 API | noop，文档说明 |
| PyInstaller 打包 | macOS 路径与 Windows 不同 | Phase 6 单列 PR |

## 4. 风险与缓解

| 风险 | 触发条件 | 缓解 |
|---|---|---|
| 云客户端窗口标题变更 | 各家厂商迭代版本 | 已有 `custom_win_title` 设置项；文档列举常见标题 |
| 客户端 UI 覆盖层遮住游戏内容 | 客户端自带 HUD | 在文档里说明需要客户端进入"纯净模式"或关闭浮窗 |
| 分辨率非 1920x1080 | 客户端默认窗口尺寸 | 文档要求用户把云客户端窗口调整到 1920x1080；或在 `client_to_screen` 后做等比缩放 |
| 帧率波动导致截图错位 | 高延迟 / 卡顿 | 已有 `.debug/images/` 缓存；让 OCR / YOLO 间隔可配 |
| macOS 屏幕录制权限未授权 | 首次启动 | 启动时检测 `Quartz.CGRequestScreenCaptureAccess`，缺失则用 `QMessageBox` 引导用户去系统设置授权 |
| 辅助功能权限未授权 | pynput 全局监听需要 | 同上引导 |
| 黑色 dock 图标不显示 | 没有 .icns | Phase 6 提供 `app.icns` 与 `Info.plist` |
| `pyobjc` 体积大 | 增加 ~50MB | 拆 `[macos]` extra，按需安装 |

## 5. 里程碑（建议）

- **M1（1 周）**：Phase 0 + Phase 1 + Phase 2 + Phase 3。GUI 能在 macOS 上拉起来，截图 + 前台点击跑通，非战斗场景（吃面 / 委托）能跑完。
- **M2（0.5 周）**：Phase 4 + Phase 5。OCR / YOLO 在 macOS 推理跑通，UI 隐藏不可用项。
- **M3（0.5 周）**：Phase 6 + Phase 7。文档、启动脚本、回归测试。
- **M4（持续）**：根据云游戏实际跑图情况，调整延迟补偿、闪避阈值。

## 6. 立即可做的预演（验证思路）

在动手改架构前，可以先用 2 小时做一次"预演"，验证云游戏假设：
1. 启动一个 macOS + 云游戏窗口（任意一个你账号有的）。
2. 新建一个 30 行 Python 脚本：
   - 用 `Quartz.CGWindowListCopyWindowInfo` 找到云客户端窗口，确认能拿到 `kCGWindowBounds`。
   - 用 `mss` 按这个 rect 截图，存 PNG，肉眼对照确认是云端游戏画面。
   - 用 `pyautogui.click(x, y)`，观察云端游戏内是否收到点击。
3. 测量端到端延迟（`pyautogui.click` 到 `mss.grab` 看到新画面的间隔），写到本文档的"实测延迟"段落，作为 Phase 6 延迟补偿的输入。

如果预演失败（截图拿到的是黑屏 / 点击云端无响应），整个方案需要重评估，**不要**在不确定云客户端行为的情况下推进 Phase 1。

## 7. 决策记录（模板）

迁移过程中遇到"我应该 X 还是 Y"时，按下面格式追加到本文档末尾：

```
### DR-001: xxx
- 日期：YYYY-MM-DD
- 状态：proposed / accepted / deprecated
- 背景：xxx
- 选项：A / B
- 决定：A
- 后果：xxx
```

---

## 附录 A：关键文件变更预览

```
新增：
  src/one_dragon/platform/__init__.py
  src/one_dragon/platform/window_service.py
  src/one_dragon/platform/input_service.py
  src/one_dragon/platform/screenshot_service.py
  src/one_dragon/platform/clipboard_service.py
  src/one_dragon/platform/overlay_service.py
  src/one_dragon/platform/hotkey_service.py
  src/one_dragon/platform/dialog_service.py
  src/one_dragon/platform/console_service.py
  src/one_dragon/platform/_impl/windows/{window,input,screenshot,clipboard,overlay,hotkey,dialog,console}_service.py
  src/one_dragon/platform/_impl/macos/{window,input,screenshot,clipboard,overlay,hotkey,dialog,console}_service.py
  scripts/install_macos_brew_deps.sh
  scripts/run_dev.sh
  .env.sample.sh
  docs/develop/zzz/cloud_e2e_report.md
  tests/one_dragon/platform/test_*.py

修改（业务侧尽量保持 import 兼容）：
  pyproject.toml                                       # 拆依赖、environments
  src/one_dragon/base/controller/pc_controller_base.py  # 后台/手柄/flash 走 noop
  src/one_dragon/base/controller/pc_game_window.py      # 走 WindowService
  src/one_dragon/base/controller/pc_screenshot/pc_screenshot_controller.py  # 平台注册
  src/one_dragon/envs/env_config.py                     # 推理后端选择
  src/one_dragon/yolo/onnx_model_loader.py              # 平台选 provider
  src/onnxocr/predict_base.py                           # 同上
  src/one_dragon/utils/gpu_executor.py                  # 串行化策略
  src/one_dragon/utils/debug_utils.py                   # 剪贴板走 service
  src/one_dragon/devtools/python_launcher.py            # JobObject 走 Windows only
  src/one_dragon/launcher/runtime_launcher.py           # console hide / MessageBox 走 service
  src/one_dragon_qt/overlay/utils/win32_utils.py        # OverlayService
  src/one_dragon_qt/overlay/overlay_manager.py          # import 切换
  src/one_dragon_qt/overlay/overlay_window.py           # import 切换
  src/one_dragon_qt/view/setting/setting_custom_interface.py
  src/one_dragon_qt/view/setting/setting_env_interface.py
  src/zzz_od/gui/app.py                                 # MessageBoxW → service
  src/zzz_od/auto_battle/auto_battle_dodge_context.py   # soundcard → sounddevice
  src/zzz_od/gui/view/setting/setting_game_interface.py # 隐藏后台/HDR/启动参数
  src/zzz_od/win_exe/runtime_launcher.py                # 通用化
  src/zzz_od/context/zzz_context.py                     # 平台分支选 controller

移除（不删，挪到 _impl/windows/）：
  散落在业务里的 ctypes.windll.* / win32api / win32gui / pywintypes 直接调用
```

## 附录 B：参考链接

- PyObjC Quartz: https://developer.apple.com/documentation/coregraphics
- NSPasteboard: https://developer.apple.com/documentation/appkit/nspasteboard
- mss 跨平台: https://python-mss.readthedocs.io/
- pynput macOS 权限: https://pynput.readthedocs.io/en/latest/limitations.html
- BlackHole 虚拟音频: https://github.com/ExistentialAudio/BlackHole
- onnxruntime Execution Providers: https://onnxruntime.ai/docs/execution-providers/
- 现有 Win32 抽象风格参考：`src/one_dragon/utils/gpu_executor.py`（已按平台特性做工厂 + 串行化）
