from __future__ import annotations

from typing import ClassVar

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QVBoxLayout, QWidget
from qfluentwidgets import (
    FlyoutViewBase,
    HyperlinkLabel,
    SettingCard,
    TeachingTipTailPosition,
)

from one_dragon_qt.utils.layout_utils import Margins
from one_dragon_qt.widgets.teaching_tip import TeachingTip


class AppSettingFlyout(FlyoutViewBase):
    """应用配置弹出框基类。

    子类需实现:
    - ``_setup_ui(layout)``: 往 QVBoxLayout 中添加控件。
    - ``init_config()``: 读取配置并初始化控件值。

    基类提供 ``self.card_margins`` 供子类创建 SettingCard 时使用，
    并自动去掉所有 SettingCard 的边框背景。

    当传入 ``app_id`` 且该 app 在 notify_config.app_map 中时,基类会自动在
    Flyout 底部追加\"通知设置\"链接,点击弹出 AppNotifySettingFlyout。
    """

    _current_tip: ClassVar[TeachingTip | None] = None

    def __init__(self, ctx, group_id: str, parent=None, app_id: str | None = None):
        FlyoutViewBase.__init__(self, parent)
        self.ctx = ctx
        self.group_id = group_id
        self.app_id: str | None = app_id
        self.card_margins = Margins(8, 4, 0, 8)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        self._setup_ui(layout)

        # 去掉 SettingCard 在 flyout 中多余的卡片边框和背景
        for card in self.findChildren(SettingCard):
            card.paintEvent = lambda _e: None

        # UX-A02: 如果该应用支持通知配置,在底部追加通知设置链接
        if self.app_id is not None and self.app_id in self.ctx.notify_config.app_map:
            self._setup_notify_link(layout)

    def _setup_notify_link(self, layout: QVBoxLayout) -> None:
        """在 Flyout 底部追加通知设置链接,点击弹出 AppNotifySettingFlyout。"""
        layout.addSpacing(8)
        link = HyperlinkLabel(url='', text='')
        link.setText('通知设置 →')
        link.linkActivated.connect(lambda: self._open_notify_flyout())
        layout.addWidget(link, 0, Qt.AlignmentFlag.AlignRight)

    def _open_notify_flyout(self) -> None:
        """打开该应用的通知设置 Flyout。"""
        if self.app_id is None:
            return
        from one_dragon_qt.widgets.app_setting.app_notify_setting_flyout import (
            AppNotifySettingFlyout,
        )
        app_name = self.ctx.notify_config.app_map.get(self.app_id, self.app_id)
        AppNotifySettingFlyout.show_flyout(
            ctx=self.ctx,
            app_id=self.app_id,
            app_name=app_name,
            target=self,
            parent=self.window(),
        )

    def backgroundColor(self) -> QColor:
        return QColor(0, 0, 0, 0)

    def borderColor(self) -> QColor:
        return QColor(0, 0, 0, 0)

    # ---------- 子类实现 ----------

    def _setup_ui(self, layout: QVBoxLayout) -> None:
        raise NotImplementedError

    def init_config(self) -> None:
        raise NotImplementedError

    # ---------- 统一显示逻辑 ----------

    @classmethod
    def show_flyout(
        cls,
        ctx,
        group_id: str,
        target: QWidget,
        parent: QWidget | None = None,
        app_id: str | None = None,
    ) -> TeachingTip:
        """显示配置弹出框，防止重复弹出。"""
        # 读取基类上的共享引用，确保所有子类互斥
        prev = AppSettingFlyout._current_tip
        if prev is not None:
            try:
                if prev.isVisible():
                    prev.close()
            except RuntimeError:
                pass
            AppSettingFlyout._current_tip = None

        content_view = cls(ctx, group_id, parent, app_id=app_id)
        content_view.init_config()

        tip = TeachingTip.make(
            view=content_view,
            target=target,
            duration=-1,
            tailPosition=TeachingTipTailPosition.RIGHT,
            parent=parent,
        )

        AppSettingFlyout._current_tip = tip
        tip.destroyed.connect(lambda: setattr(AppSettingFlyout, '_current_tip', None))
        return tip
