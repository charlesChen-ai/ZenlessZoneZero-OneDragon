"""macOS 平台剪贴板：NSPasteboard。"""

from __future__ import annotations

import io

from cv2.typing import MatLike
from PIL import Image

from one_dragon.platform.clipboard_service import ClipboardService
from one_dragon.utils.log_utils import log


class MacosClipboardService(ClipboardService):

    def _pb(self):
        from AppKit import NSPasteboard
        return NSPasteboard.generalPasteboard()

    def set_text(self, text: str) -> None:
        try:
            from AppKit import NSString
            pb = self._pb()
            pb.clearContents()
            pb.setString_forType_(NSString.stringWithString_(text), 'public.utf8-plain-text')
        except Exception as e:
            log.warning('写入剪贴板文本失败: %s', e)

    def get_text(self) -> str:
        try:
            pb = self._pb()
            data = pb.stringForType_('public.utf8-plain-text')
            if data is None:
                return ''
            return str(data)
        except Exception:
            return ''

    def clear(self) -> None:
        try:
            self._pb().clearContents()
        except Exception as e:
            log.warning('清空剪贴板失败: %s', e)

    def set_image(self, image: MatLike) -> None:
        try:
            pil_img = Image.fromarray(image)
            with io.BytesIO() as buf:
                pil_img.save(buf, 'PNG')
                data = buf.getvalue()
            from AppKit import NSData
            ns_data = NSData.dataWithBytes_length_(data, len(data))
            pb = self._pb()
            pb.clearContents()
            pb.setData_forType_(ns_data, 'public.png')
        except Exception as e:
            log.warning('写入剪贴板图片失败: %s', e)
