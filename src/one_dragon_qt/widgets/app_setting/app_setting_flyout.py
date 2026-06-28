from __future__ import annotations

from typing import ClassVar

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget
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

    当传入 ``app_id`` 时,基类在 Flyout 底部追加运行快捷操作行:
    - 如果该 app 在 notify_config.app_map 中,左侧显示"通知设置"链接
    - 右侧显示"移到顶部"按钮,点击后调用 ctx.move_app_to_top 并关闭 Flyout
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

        # UX-A02 + UX-A01 Phase 2: 底部追加通知链接 + 移到顶部按钮
        if self.app_id is not None:
            self._setup_run_actions(layout)

    def _setup_run_actions(self, layout: QVBoxLayout) -> None:
        """在 Flyout 底部追加"通知设置"链接 + "移到顶部"按钮。"""
        from qfluentwidgets import FluentIcon, PushButton

        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)

        if self.app_id in self.ctx.notify_config.app_map:
            notify_link = HyperlinkLabel(url='', text='通知设置')
            notify_link.linkActivated.connect(self._open_notify_flyout)
            actions_layout.addWidget(notify_link, 0, Qt.AlignmentFlag.AlignLeft)
        else:
            actions_layout.addStretch(1)

        move_top_btn = PushButton('移到顶部', self, FluentIcon.PIN)
        move_top_btn.clicked.connect(self._on_move_top_clicked)
        actions_layout.addWidget(move_top_btn, 0, Qt.AlignmentFlag.AlignRight)

        layout.addSpacing(8)
        layout.addLayout(actions_layout)

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

    def _on_move_top_clicked(self) -> None:
        """把当前 app 移到一条龙运行列表顶部,然后关闭 Flyout。"""
        if self.app_id is None:
            return
        self.ctx.move_app_to_top(self.app_id)
        AppSettingFlyout._close_current_tip()

    @classmethod
    def _close_current_tip(cls) -> None:
        """关闭当前 Flyout(如果存在)。"""
        prev = cls._current_tip
        if prev is None:
            return
        try:
            if prev.isVisible():
                prev.close()
        except RuntimeError:
            pass
        cls._current_tip = None

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
