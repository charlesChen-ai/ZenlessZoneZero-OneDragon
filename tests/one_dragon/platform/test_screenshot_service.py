"""截图服务组合策略测试。"""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("cv2")

from one_dragon.base.geometry.rectangle import Rect
from one_dragon.platform.screenshot_service import (
    CompositeScreenshotService,
    ScreenshotService,
)


class FakeScreenshotService(ScreenshotService):

    def __init__(
            self,
            *,
            available: bool = True,
            return_value=None,
            raise_exc: BaseException | None = None,
            name: str = "fake",
    ) -> None:
        self._available = available
        self._return_value = return_value
        self._raise_exc = raise_exc
        self._name = name
        self.capture_calls: list[Rect] = []

    @property
    def method_name(self) -> str:
        return self._name

    def is_available(self) -> bool:
        return self._available

    def capture(self, rect: Rect):
        self.capture_calls.append(rect)
        if self._raise_exc is not None:
            raise self._raise_exc
        return self._return_value


def test_composite_with_empty_services_returns_none() -> None:
    composite = CompositeScreenshotService([])
    assert composite.capture(Rect(0, 0, 100, 100)) is None


def test_composite_single_service_returns_array() -> None:
    expected = np.zeros((10, 10, 3), dtype=np.uint8)
    fake = FakeScreenshotService(return_value=expected)
    composite = CompositeScreenshotService([fake])

    rect = Rect(0, 0, 100, 100)
    result = composite.capture(rect)

    assert result is expected
    assert fake.capture_calls == [rect]


def test_composite_skips_unavailable_services() -> None:
    expected = np.zeros((10, 10, 3), dtype=np.uint8)
    unavailable = FakeScreenshotService(available=False, return_value=expected)
    available = FakeScreenshotService(available=True, return_value=expected)
    composite = CompositeScreenshotService([unavailable, available])

    rect = Rect(0, 0, 100, 100)
    composite.capture(rect)

    assert unavailable.capture_calls == []
    assert available.capture_calls == [rect]


def test_composite_skips_raising_services_and_returns_first_non_none() -> None:
    expected = np.zeros((10, 10, 3), dtype=np.uint8)
    raising = FakeScreenshotService(raise_exc=RuntimeError("boom"))
    returning_none = FakeScreenshotService(return_value=None)
    returning_array = FakeScreenshotService(return_value=expected)
    composite = CompositeScreenshotService(
        [raising, returning_none, returning_array],
    )

    rect = Rect(0, 0, 100, 100)
    result = composite.capture(rect)

    assert result is expected
    assert len(raising.capture_calls) == 1
    assert len(returning_none.capture_calls) == 1
    assert len(returning_array.capture_calls) == 1


def test_composite_skips_services_returning_none_and_returns_first_non_none() -> None:
    expected = np.zeros((10, 10, 3), dtype=np.uint8)
    first = FakeScreenshotService(return_value=None)
    second = FakeScreenshotService(return_value=expected)
    composite = CompositeScreenshotService([first, second])

    result = composite.capture(Rect(0, 0, 50, 50))

    assert result is expected
    assert len(first.capture_calls) == 1
    assert len(second.capture_calls) == 1


def test_composite_all_unavailable_returns_none() -> None:
    composite = CompositeScreenshotService([
        FakeScreenshotService(available=False, return_value=np.zeros((2, 2, 3), dtype=np.uint8)),
        FakeScreenshotService(available=False, return_value=np.zeros((2, 2, 3), dtype=np.uint8)),
    ])
    assert composite.capture(Rect(0, 0, 100, 100)) is None


def test_composite_all_raise_returns_none() -> None:
    composite = CompositeScreenshotService([
        FakeScreenshotService(raise_exc=RuntimeError("a")),
        FakeScreenshotService(raise_exc=ValueError("b")),
    ])
    assert composite.capture(Rect(0, 0, 100, 100)) is None


def test_composite_available_methods_lists_only_available() -> None:
    services = [
        FakeScreenshotService(available=True, name="a"),
        FakeScreenshotService(available=False, name="b"),
        FakeScreenshotService(available=True, name="c"),
    ]
    composite = CompositeScreenshotService(services)

    assert composite.available_methods == ["a", "c"]


def test_composite_stops_after_first_non_none_result() -> None:
    expected = np.zeros((4, 4, 3), dtype=np.uint8)
    first = FakeScreenshotService(return_value=expected)
    second = FakeScreenshotService(return_value=expected)
    composite = CompositeScreenshotService([first, second])

    composite.capture(Rect(0, 0, 100, 100))

    assert len(first.capture_calls) == 1
    assert second.capture_calls == []
