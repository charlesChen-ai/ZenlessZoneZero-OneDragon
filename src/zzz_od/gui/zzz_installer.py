import os
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from qfluentwidgets import Theme, setTheme

from one_dragon_qt.app.directory_picker import DirectoryPickerWindow
from one_dragon_qt.utils.icon_utils import get_platform_app_icon

if __name__ == '__main__':
    app = QApplication(sys.argv)
    setTheme(Theme['AUTO'])

    icon_name = get_platform_app_icon()
    if icon_name is not None:
        if hasattr(sys, '_MEIPASS'):
            icon_path = Path(sys._MEIPASS) / f'resources/assets/ui/{icon_name}'
        else:
            icon_path = Path.cwd() / f'assets/ui/{icon_name}'
    else:
        icon_path = None
    installer_dir = Path(sys.argv[0]).resolve().parent

    picker_window = DirectoryPickerWindow(icon_path=icon_path, installer_dir=str(installer_dir))
    picker_window.exec()
    work_dir = picker_window.selected_directory
    if not work_dir:
        sys.exit(0)
    os.chdir(work_dir)

    # 延迟导入
    from one_dragon.base.operation.one_dragon_env_context import OneDragonEnvContext
    from one_dragon.utils.i18_utils import detect_and_set_default_language, gt
    from zzz_od.gui.zzz_installer_window import ZInstallerWindow

    _ctx = OneDragonEnvContext()
    _ctx.installer_dir = str(installer_dir)
    detect_and_set_default_language()
    w = ZInstallerWindow(_ctx, gt(f'{_ctx.project_config.project_name}-installer'))
    w.show()
    app.exec()
    _ctx.after_app_shutdown()
