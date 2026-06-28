from __future__ import annotations

from one_dragon.base.geometry.point import Point
from one_dragon.base.geometry.rectangle import Rect
from one_dragon.platform.window_service import WindowInfo
from one_dragon.utils.log_utils import log


class PcGameWindow:

    def __init__(self,
                 standard_width: int = 1920,
                 standard_height: int = 1080):
        from one_dragon.platform import get_platform_context
        self._platform_window = get_platform_context().window
        self.win_title: str | None = None
        self.standard_width: int = standard_width
        self.standard_height: int = standard_height
        self.standard_game_rect: Rect = Rect(0, 0, standard_width, standard_height)

        self._info: WindowInfo | None = None

    def _clear_cached_window(self) -> None:
        self._info = None

    def init_win(self) -> None:
        if self.win_title is None:
            return
        self._info = self._platform_window.find_by_title(self.win_title)

    def update_win_title(self, new_title: str) -> None:
        if self.win_title != new_title:
            self.win_title = new_title
            self._clear_cached_window()

    def refresh_win(self) -> None:
        self._clear_cached_window()
        self.init_win()

    def get_win(self):
        return self._info

    def get_hwnd(self) -> int:
        if self._info is None:
            self.init_win()
        return int(self._info.handle) if self._info is not None else 0

    def _current_window_info(self) -> WindowInfo | None:
        if self._info is None:
            self.init_win()
        return self._info

    def _reset_cached_window(self) -> None:
        self._info = None

    @property
    def is_win_valid(self) -> bool:
        info = self._current_window_info()
        if info is None:
            return False
        return self._platform_window.is_window_valid(info)

    @property
    def is_win_active(self) -> bool:
        fg = self._platform_window.get_foreground()
        if fg is None or self._info is None:
            return False
        return int(fg.handle) == int(self._info.handle)

    @property
    def is_win_scale(self) -> bool:
        win_rect = self.win_rect
        if win_rect is None:
            return False
        return not (win_rect.width == self.standard_width and win_rect.height == self.standard_height)

    def active(self) -> bool:
        info = self._current_window_info()
        if info is None:
            return False
        if self.is_win_active:
            return True
        try:
            self._platform_window.restore(info)
            return self._platform_window.activate(info)
        except Exception as e:
            log.warning('激活窗口失败: %s', e)
            self._reset_cached_window()
            return False

    @property
    def win_rect(self) -> Rect | None:
        info = self._current_window_info()
        if info is None:
            return None
        rect = self._platform_window.get_client_rect(info)
        if rect is None or rect.width <= 0 or rect.height <= 0:
            return None
        if rect.x1 <= -30000 and rect.y1 <= -30000:
            return None
        return rect

    def get_scaled_game_pos(self, game_pos: Point) -> Point | None:
        rect = self.win_rect
        if rect is None or self.standard_game_rect is None:
            return None
        if self.is_win_scale:
            sx = game_pos.x * (rect.width / self.standard_width)
            sy = game_pos.y * (rect.height / self.standard_height)
            return Point(int(sx), int(sy))
        return Point(game_pos.x - self.standard_game_rect.x1, game_pos.y - self.standard_game_rect.y1)

    def is_game_pos_in_game_rect(self, s_pos: Point) -> bool:
        rect = self.win_rect
        if rect is None:
            rect = self.standard_game_rect
        return 0 <= s_pos.x < rect.width and 0 <= s_pos.y < rect.height

    def game2win_pos(self, game_pos: Point) -> Point | None:
        rect = self.win_rect
        if rect is None:
            return None
        gp: Point | None = self.get_scaled_game_pos(game_pos)
        return rect.left_top + gp if gp is not None else None
