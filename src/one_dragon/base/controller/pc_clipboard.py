from __future__ import annotations

import time

from pynput.keyboard import Controller, Key

from one_dragon.platform import get_platform_context
from one_dragon.utils.log_utils import log, mask_text


class PcClipboard:

    @staticmethod
    def _clip():
        return get_platform_context().clipboard

    @staticmethod
    def copy_and_paste(text: str) -> None:
        PcClipboard.copy_string(text)
        PcClipboard.paste_text()
        PcClipboard.empty_clipboard()

    @staticmethod
    def empty_clipboard() -> None:
        PcClipboard._clip().clear()

    @staticmethod
    def copy_string(text: str) -> None:
        log.info(f'复制文字到剪切板:{mask_text(text)}')
        PcClipboard._clip().set_text(text)
        log.info('复制文字到剪切板成功')

    @staticmethod
    def paste_text() -> str:
        keyboard = Controller()
        data = PcClipboard._clip().get_text()
        log.info(f'粘贴文字, 获取到:{mask_text(data)}')

        log.info('粘贴文字, 按下 Ctrl+V')
        log.debug('粘贴文字, 按下 Ctrl')
        with keyboard.pressed(Key.ctrl):
            time.sleep(0.2)
            log.debug('粘贴文字, 按下 V')
            keyboard.press('v')
            time.sleep(0.2)
            log.debug('粘贴文字, 释放 V')
            keyboard.release('v')

        return data
