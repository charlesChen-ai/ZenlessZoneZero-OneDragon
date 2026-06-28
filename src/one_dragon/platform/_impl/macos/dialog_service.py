"""macOS 平台对话框：NSAlert。"""

from __future__ import annotations

from one_dragon.platform.dialog_service import DialogService
from one_dragon.utils.log_utils import log


class MacosDialogService(DialogService):

    def _alert(self, title: str, message: str, style: str) -> int:
        try:
            from AppKit import (
                NSAlert,
                NSCriticalAlertStyle,
                NSInformationalAlertStyle,
                NSWarningAlertStyle,
            )
            style_map = {
                'info': NSInformationalAlertStyle,
                'warning': NSWarningAlertStyle,
                'error': NSCriticalAlertStyle,
            }
            alert = NSAlert.alloc().init()
            alert.setMessageText_(title)
            alert.setInformativeText_(message)
            alert.setAlertStyle_(style_map.get(style, NSInformationalAlertStyle))
            return int(alert.runModal())
        except Exception as e:
            log.warning('NSAlert 弹窗失败: %s', e)
            print(f'[{style.upper()}] {title}: {message}')
            return 0

    def show_error(self, title: str, message: str) -> None:
        self._alert(title, message, 'error')

    def show_warning(self, title: str, message: str) -> None:
        self._alert(title, message, 'warning')

    def show_info(self, title: str, message: str) -> None:
        self._alert(title, message, 'info')

    def confirm(self, title: str, message: str) -> bool:
        try:
            from AppKit import NSAlert
            alert = NSAlert.alloc().init()
            alert.setMessageText_(title)
            alert.setInformativeText_(message)
            alert.addButtonWithTitle_('确定')
            alert.addButtonWithTitle_('取消')
            return int(alert.runModal()) == 1000  # NSAlertFirstButtonReturn
        except Exception as e:
            log.warning('NSAlert confirm 失败: %s', e)
            return False
