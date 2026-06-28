import logging
import re
from collections import deque

from PySide6.QtCore import QEvent, QObject, QTimer, Signal
from PySide6.QtGui import (
    QColor,
    QKeySequence,
    QMouseEvent,
    QShortcut,
    QTextCharFormat,
    QTextCursor,
)
from qfluentwidgets import LineEdit, PlainTextEdit, isDarkTheme

from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log as od_log
from one_dragon.yolo.log_utils import log as yolo_log


class LogSignal(QObject):
    new_log = Signal(str)

class LogReceiver(logging.Handler):
    def __init__(self):
        super().__init__()
        # 限制日志数量
        self.log_list: deque[str] = deque(maxlen=64)
        # 新日志
        self.new_logs: list[str] = []
        # 是否接收日志
        self.update = False

    def emit(self, record):
        """将新日志记录添加到日志队列"""
        # 不接收日志时直接返回
        if not self.update:
            return
        msg = self.format(record)
        self.log_list.append(msg)
        self.new_logs.append(msg)

    def get_new_logs(self) -> list[str]:
        """获取新的日志"""
        new_logs = self.new_logs.copy()
        self.new_logs.clear()
        return new_logs

    def clear_logs(self):
        """清空日志队列"""
        self.log_list.clear()
        self.new_logs.clear()


class LogDisplayCard(PlainTextEdit):
    userWheelScroll = Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        # 设置只读
        self.setReadOnly(True)

        # 初始化颜色
        self.init_color()

        # 初始化接收器
        self.receiver = LogReceiver()
        od_log.addHandler(self.receiver)
        yolo_log.addHandler(self.receiver)

        # 初始化定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_logs)

        # 初始化滚动重置定时器
        self.scroll_reset_timer = QTimer(self)
        self.scroll_reset_timer.setSingleShot(True)
        self.scroll_reset_timer.timeout.connect(self._enable_auto_scroll)

        self._mouse_button_down = False
        self.userWheelScroll.connect(self._on_user_wheel_scroll)
        self.verticalScrollBar().valueChanged.connect(self.handle_scroll_change)

        # 设置自动滚动
        self.auto_scroll = False

        # 更新频率(毫秒)
        self.update_frequency = 100

        # 日志是否运行
        self.is_running = False

        # 暂停标记
        self.is_pause = False

        # 限制显示行数
        self.setMaximumBlockCount(192)

        # ---- 搜索栏 (浮层,默认隐藏,Ctrl+F 显示) ----
        self.search_bar = LineEdit(self)
        self.search_bar.setPlaceholderText(gt('搜索日志'))
        self.search_bar.setMaximumWidth(280)
        self.search_bar.hide()
        self.search_bar.textChanged.connect(self._on_search_changed)
        self.search_bar.installEventFilter(self)
        self._search_term: str = ''
        self._search_shortcut = QShortcut(QKeySequence('Ctrl+F'), self, activated=self._show_search_bar)
        self._close_search_shortcut = QShortcut(QKeySequence('Escape'), self, activated=self._hide_search_bar)

    def init_color(self):
        """根据主题设置颜色"""
        if isDarkTheme():
            self._color = '#00D9A3'  # 绿色(方括号内容)
            self._error_color = '#FF6B6B'  # 红色(错误关键字)
        else:
            self._color = '#00A064'  # 绿色(方括号内容)
            self._error_color = '#E74C3C'  # 红色(错误关键字)

    def start(self, clear_log: bool = False):
        """启动日志显示"""
        if clear_log:
            self.receiver.clear_logs()
            self.clear()
        self.init_color()
        self.receiver.update = True
        if not self.is_running:
            self.is_running = True
        if not self.is_pause:
            self.receiver.clear_logs()
            self.clear()
        self.auto_scroll = True
        self.update_timer.start(self.update_frequency)

    def pause(self):
        """停止日志显示"""
        if self.is_running:
            self.is_running = False
        self.is_pause = True
        self.auto_scroll = False
        self.update_timer.stop()
        self.scroll_reset_timer.stop()
        self.receiver.update = False

    def stop(self):
        """停止日志显示"""
        if self.is_running:
            self.is_running = False
        if self.is_pause:
            self.is_pause = False
        self.auto_scroll = False
        self.update_timer.stop()
        self.scroll_reset_timer.stop()
        self.update_logs()  # 停止后 最后更新一次日志
        self.receiver.update = False

    def update_logs(self) -> None:
        """更新日志显示区域"""
        new_logs = self.receiver.get_new_logs()
        # 格式化日志
        if len(new_logs) != 0:
            formatted_logs = self._format_logs(new_logs)
            self.appendHtml(formatted_logs)
        if self.auto_scroll:
            self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())  # 滚动到最新位置

    def mousePressEvent(self, event: QMouseEvent):
        """处理鼠标点击事件"""
        self._mouse_button_down = True
        self.auto_scroll = False
        super().mousePressEvent(event)
        self.scroll_reset_timer.stop()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """处理鼠标释放事件"""
        self._mouse_button_down = False
        super().mouseReleaseEvent(event)
        self.scroll_reset_timer.start(15000)  # 15秒

    def _on_user_wheel_scroll(self):
        """处理用户滚轮滚动事件"""
        self.auto_scroll = False
        self.scroll_reset_timer.start(15000)  # 15秒

    def _enable_auto_scroll(self):
        """在用户滚动一段时间后恢复自动滚动"""
        if self.is_running and not self.is_pause and not self.textCursor().hasSelection():
            self.auto_scroll = True

    def handle_scroll_change(self, value: int):
        """处理滚动条值变化事件"""
        if self._mouse_button_down:  # 如果鼠标按钮仍被按下，则不恢复自动滚动
            return

        scrollbar = self.verticalScrollBar()
        is_at_bottom = scrollbar.value() == scrollbar.maximum()
        is_scrollable = scrollbar.maximum() > scrollbar.minimum()

        if not self.auto_scroll:
            if is_at_bottom and is_scrollable:
                if self.is_running and not self.is_pause:
                    self.auto_scroll = True
                self.scroll_reset_timer.stop()

    def eventFilter(self, obj, event: QEvent):
        if event.type() == QEvent.Type.Wheel:
            self.userWheelScroll.emit()
        return super().eventFilter(obj, event)

    def _format_logs(self, log_list: list[str]) -> str:
        """格式化日志"""
        formatted_logs = []
        formatted_log = ""

        for log_item in log_list:
            formatted_log = log_item

            # 1. 先处理红色错误关键字
            error_keywords = ['失败', '错误', '异常', '警告', 'ERROR', 'WARNING', 'FAIL', 'Exception', 'Error']
            for keyword in error_keywords:
                if keyword in formatted_log:
                    formatted_log = formatted_log.replace(
                        keyword,
                        f'<span style="color: {self._error_color}; font-weight: bold;">{keyword}</span>'
                    )

            # 2. 再处理绿色方括号内容(注意避免重复处理已经有HTML标签的部分)
            if '[' in log_item and ']' in log_item:
                # 使用正则表达式来更精确地处理方括号，避免与HTML标签冲突

                pattern = r'\[([^\]]+)\]'

                def replace_brackets(match):
                    content = match.group(1)
                    # 检查是否已经被HTML标签包围(避免重复处理)
                    if '<span' in content or '</span>' in content:
                        return match.group(0)  # 返回原始内容
                    return f'[<span style="color: {self._color};">{content}</span>]'

                formatted_log = re.sub(pattern, replace_brackets, formatted_log)

            formatted_logs.append(formatted_log)

        # 检查是否有日志
        if len(log_list) <= 1:
            return formatted_log
        else:
            return '<br>'.join(formatted_logs)

    # ------------------- 搜索 ------------------- #

    def resizeEvent(self, event) -> None:
        """窗口尺寸变化时,把搜索栏定位到右上角。"""
        super().resizeEvent(event)
        self._position_search_bar()

    def _position_search_bar(self) -> None:
        """把搜索栏定位到右上角。"""
        if self.search_bar.isVisible():
            margin = 8
            self.search_bar.move(
                self.width() - self.search_bar.width() - margin,
                margin,
            )

    def _show_search_bar(self) -> None:
        """Ctrl+F: 显示并聚焦搜索栏。"""
        self.search_bar.show()
        self.search_bar.setFocus()
        self.search_bar.selectAll()
        self._position_search_bar()

    def _hide_search_bar(self) -> None:
        """Esc: 隐藏搜索栏并清空搜索。"""
        self.search_bar.clear()
        self.search_bar.hide()
        self._clear_search_highlight()
        self.setFocus()

    def _on_search_changed(self, term: str) -> None:
        """搜索词变化时,实时高亮所有匹配位置。"""
        self._search_term = term
        self._apply_search_highlight()

    def _apply_search_highlight(self) -> None:
        """在 PlainTextEdit 中高亮所有 _search_term 出现的位置。"""
        self._clear_search_highlight()
        if not self._search_term:
            return
        fmt = QTextCharFormat()
        fmt.setBackground(QColor(255, 213, 79))  # 黄色高亮
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        doc = self.document()
        idx = 0
        while True:
            found_cursor = doc.find(self._search_term, idx)
            if found_cursor.isNull():
                break
            extra = type(self.ExtraSelection())()  # type: ignore[attr-defined]
            extra.cursor = found_cursor
            extra.format = fmt
            self.setExtraSelections([extra])
            idx = found_cursor.selectionEnd()
            if idx >= doc.characterCount():
                break

    def _clear_search_highlight(self) -> None:
        """清空搜索高亮。"""
        self.setExtraSelections([])
