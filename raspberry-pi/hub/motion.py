"""Debounce czujnika PIR."""

from __future__ import annotations

import logging
import threading
from typing import Callable

log = logging.getLogger(__name__)


class MotionDetector:
    """Ruch jest zgłaszany od razu, koniec ruchu dopiero po clear_s bez sygnału z czujnika.

    Krótkie przerwy i zakłócenia w trakcie ruchu nie generują serii zdarzeń.
    """

    def __init__(self, clear_s: float, publish: Callable[[bool], None]) -> None:
        self._clear_s = clear_s
        self._publish = publish
        self._lock = threading.Lock()
        self._active = False
        self._timer: threading.Timer | None = None
        # Zwiększany przy każdym sygnale ruchu: unieważnia timer, który już wystartował.
        self._generation = 0

    @property
    def active(self) -> bool:
        return self._active

    def on_input(self, level: bool) -> None:
        with self._lock:
            if level:
                self._generation += 1
                self._cancel_timer()
                if not self._active:
                    self._active = True
                    log.info("Wykryto ruch")
                    self._publish(True)
            elif self._active and self._timer is None:
                self._timer = threading.Timer(self._clear_s, self._clear, args=(self._generation,))
                self._timer.daemon = True
                self._timer.start()

    def _clear(self, generation: int) -> None:
        with self._lock:
            if generation != self._generation or not self._active:
                return
            self._timer = None
            self._active = False
            log.info("Koniec ruchu")
            self._publish(False)

    def _cancel_timer(self) -> None:
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

    def close(self) -> None:
        with self._lock:
            self._generation += 1
            self._cancel_timer()
