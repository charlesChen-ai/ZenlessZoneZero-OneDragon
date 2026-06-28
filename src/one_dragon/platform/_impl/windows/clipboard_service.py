"""Windows 平台剪贴板。"""

from __future__ import annotations

import contextlib
import io

import pywintypes
import win32clipboard
import win32con
from cv2.typing import MatLike
from PIL import Image

from one_dragon.platform.clipboard_service import ClipboardService
from one_dragon.utils.log_utils import log


class WindowsClipboardService(ClipboardService):

    def set_text(self, text: str) -> None:
        try:
            win32clipboard.OpenClipboard()
            try:
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardText(text, win32con.CF_UNICODETEXT)
            finally:
                self._safe_close()
        except pywintypes.error as e:
            log.warning('写入剪贴板文本失败: %s', e)

    def get_text(self) -> str:
        try:
            win32clipboard.OpenClipboard()
            try:
                return win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT) or ''
            finally:
                self._safe_close()
        except pywintypes.error:
            return ''

    def clear(self) -> None:
        try:
            win32clipboard.OpenClipboard()
            try:
                win32clipboard.EmptyClipboard()
            finally:
                self._safe_close()
        except pywintypes.error as e:
            log.warning('清空剪贴板失败: %s', e)

    def set_image(self, image: MatLike) -> None:
        try:
            pil_img = Image.fromarray(image)
            with io.BytesIO() as buf:
                pil_img.save(buf, 'BMP')
                data = buf.getvalue()[14:]  # skip BMP header
            win32clipboard.OpenClipboard()
            try:
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32con.CF_DIB, data)
            finally:
                self._safe_close()
        except Exception as e:
            log.warning('写入剪贴板图片失败: %s', e)

    @staticmethod
    def _safe_close() -> None:
        with contextlib.suppress(Exception):
            win32clipboard.CloseClipboard()
