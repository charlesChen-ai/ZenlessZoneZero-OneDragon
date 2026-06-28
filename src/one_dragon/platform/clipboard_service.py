"""剪贴板服务抽象。"""

from __future__ import annotations

from abc import ABC, abstractmethod

from cv2.typing import MatLike


class ClipboardService(ABC):
    """剪贴板：文本 + 图片。"""

    @abstractmethod
    def set_text(self, text: str) -> None:
        """写入纯文本。"""

    @abstractmethod
    def get_text(self) -> str:
        """读取纯文本，失败返回空串。"""

    @abstractmethod
    def clear(self) -> None:
        """清空剪贴板。"""

    @abstractmethod
    def set_image(self, image: MatLike) -> None:
        """写入一张 RGB 图像。"""
