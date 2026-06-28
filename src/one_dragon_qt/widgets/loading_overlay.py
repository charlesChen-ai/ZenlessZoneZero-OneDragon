"""
加载遮罩组件
用于异步操作时显示半透明遮罩 + 进度环 + 文案。
"""
from __future__ import annotations

from contextlib import contextmanager

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QVBoxLayout, QWidget
from qfluentwidgets import CaptionLabel, ProgressRing, isDarkTheme

from one_dragon.utils.i18_utils import gt


class LoadingOverlay(QWidget):
    """半透明加载遮罩,内部含 ProgressRing + CaptionLabel。

    使用示例::

        overlay = LoadingOverlay.show(parent, gt('加载中...'))
        try:
            do_something_slow()
        finally:
            LoadingOverlay.hide(overlay)
    """

    def __init__(self, parent: QWidget, text: str = ''):
        super().__init__(parent)
        self._parent = parent

        # 拦截鼠标事件,避免穿透到下层控件
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        bg = QColor(0, 0, 0, 128 if isDarkTheme() else 160)
        self.setStyleSheet(f'background-color: rgba({bg.red()}, {bg.green()}, {bg.blue()}, {bg.alpha()});')

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.progress = ProgressRing(self)
        self.progress.setFixedSize(48, 48)
        layout.addWidget(self.progress, 0, Qt.AlignmentFlag.AlignCenter)

        self.label = CaptionLabel(text, self)
        self.label.setStyleSheet('color: white; font-weight: bold;')
        layout.addSpacing(12)
        layout.addWidget(self.label, 0, Qt.AlignmentFlag.AlignCenter)

        # 全屏覆盖父控件
        if parent is not None:
            self.setGeometry(parent.rect())
            self.raise_()
        self.show()
        self.progress.start()

    @staticmethod
    def show(parent: QWidget, text: str = '') -> LoadingOverlay:
        """在父控件上显示加载遮罩。"""
        overlay = LoadingOverlay(parent, gt(text) if text else '')
        return overlay

    @staticmethod
    def hide(overlay: LoadingOverlay | None) -> None:
        """关闭加载遮罩。"""
        if overlay is None:
            return
        try:
            overlay.progress.stop()
            overlay.hide()
            overlay.deleteLater()
        except RuntimeError:
            pass


@contextmanager
def with_loading(parent: QWidget, text: str = ''):
    """上下文管理器形式的加载遮罩。

    使用示例::

        with with_loading(self, '加载中...'):
            do_something_slow()
    """
    overlay = LoadingOverlay.show(parent, text)
    try:
        yield overlay
    finally:
        LoadingOverlay.hide(overlay)
