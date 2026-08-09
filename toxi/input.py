from __future__ import annotations

import pygame

try:
    import pygame._sdl2.controller as sdl_controller
except ImportError:  # pragma: no cover - only relevant on unusual pygame builds
    sdl_controller = None


class Controls:
    """Unified keyboard + SDL game-controller input.

    SDL's controller layer normalizes common Xbox, PlayStation and similar pads to
    the same A/B/X/Y + stick + d-pad layout. Keyboard input remains available as
    a fallback, but every game action also has a controller binding.
    """

    DEADZONE = 0.24
    DIGITAL_THRESHOLD = 0.58

    def __init__(self) -> None:
        self.controller = None
        self.controller_name = "Kein Controller erkannt"
        self._last_scan_ms = -10_000
        self._current: dict[str, bool] = {}
        self._previous: dict[str, bool] = {}
        self._pressed: dict[str, bool] = {}
        self._move = pygame.Vector2()
        self._connect_first(force=True)

    @property
    def connected(self) -> bool:
        return self.controller is not None and self._attached()

    def _attached(self) -> bool:
        if self.controller is None:
            return False
        try:
            return bool(self.controller.attached())
        except pygame.error:
            return False

    def _connect_first(self, force: bool = False) -> None:
        if sdl_controller is None:
            return

        now = pygame.time.get_ticks()
        if not force and now - self._last_scan_ms < 1000:
            return
        self._last_scan_ms = now

        try:
            if not sdl_controller.get_init():
                sdl_controller.init()
        except pygame.error:
            return

        if self._attached():
            return

        if self.controller is not None:
            try:
                self.controller.quit()
            except pygame.error:
                pass
            self.controller = None

        try:
            count = sdl_controller.get_count()
        except pygame.error:
            count = 0

        for index in range(count):
            try:
                if not sdl_controller.is_controller(index):
                    continue
                self.controller = sdl_controller.Controller(index)
                self.controller_name = sdl_controller.name_forindex(index) or "Game Controller"
                self._previous.clear()
                self._current.clear()
                self._pressed.clear()
                return
            except pygame.error:
                self.controller = None

        self.controller_name = "Kein Controller erkannt"

    def _button(self, name: str, fallback: int) -> bool:
        if not self.connected or sdl_controller is None:
            return False
        button = getattr(sdl_controller, name, fallback)
        try:
            return bool(self.controller.get_button(button))
        except pygame.error:
            return False

    def _axis(self, name: str, fallback: int) -> float:
        if not self.connected or sdl_controller is None:
            return 0.0
        axis = getattr(sdl_controller, name, fallback)
        try:
            raw = float(self.controller.get_axis(axis))
        except pygame.error:
            return 0.0
        value = max(-1.0, min(1.0, raw / 32767.0))
        if abs(value) < self.DEADZONE:
            return 0.0
        # Rescale the remainder so movement starts smoothly just outside the deadzone.
        sign = -1.0 if value < 0 else 1.0
        return sign * (abs(value) - self.DEADZONE) / (1.0 - self.DEADZONE)

    def update(self) -> None:
        if not self._attached():
            self._connect_first()

        keys = pygame.key.get_pressed()
        key_x = float(int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(keys[pygame.K_a] or keys[pygame.K_LEFT]))
        key_y = float(int(keys[pygame.K_s] or keys[pygame.K_DOWN]) - int(keys[pygame.K_w] or keys[pygame.K_UP]))

        stick_x = self._axis("CONTROLLER_AXIS_LEFTX", 0)
        stick_y = self._axis("CONTROLLER_AXIS_LEFTY", 1)
        dpad_x = float(
            int(self._button("CONTROLLER_BUTTON_DPAD_RIGHT", 14))
            - int(self._button("CONTROLLER_BUTTON_DPAD_LEFT", 13))
        )
        dpad_y = float(
            int(self._button("CONTROLLER_BUTTON_DPAD_DOWN", 12))
            - int(self._button("CONTROLLER_BUTTON_DPAD_UP", 11))
        )

        move_x = key_x if key_x else (dpad_x if dpad_x else stick_x)
        move_y = key_y if key_y else (dpad_y if dpad_y else stick_y)
        self._move.update(move_x, move_y)
        if self._move.length_squared() > 1.0:
            self._move = self._move.normalize()

        left = bool(keys[pygame.K_LEFT] or keys[pygame.K_a]) or dpad_x < 0 or stick_x <= -self.DIGITAL_THRESHOLD
        right = bool(keys[pygame.K_RIGHT] or keys[pygame.K_d]) or dpad_x > 0 or stick_x >= self.DIGITAL_THRESHOLD
        up = bool(keys[pygame.K_UP] or keys[pygame.K_w]) or dpad_y < 0 or stick_y <= -self.DIGITAL_THRESHOLD
        down = bool(keys[pygame.K_DOWN] or keys[pygame.K_s]) or dpad_y > 0 or stick_y >= self.DIGITAL_THRESHOLD

        a = self._button("CONTROLLER_BUTTON_A", 0)
        b = self._button("CONTROLLER_BUTTON_B", 1)
        x = self._button("CONTROLLER_BUTTON_X", 2)
        y = self._button("CONTROLLER_BUTTON_Y", 3)
        start = self._button("CONTROLLER_BUTTON_START", 6)
        back_button = self._button("CONTROLLER_BUTTON_BACK", 4)

        current = {
            "confirm": bool(keys[pygame.K_RETURN] or keys[pygame.K_SPACE]) or a or start,
            "action": bool(keys[pygame.K_SPACE]) or a or x,
            "back": bool(keys[pygame.K_ESCAPE]) or b or back_button,
            "reset": bool(keys[pygame.K_r]) or y,
            "left": left,
            "right": right,
            "up": up,
            "down": down,
        }
        self._pressed = {
            name: active and not self._previous.get(name, False)
            for name, active in current.items()
        }
        self._previous = current.copy()
        self._current = current

    def pressed(self, action: str) -> bool:
        return self._pressed.get(action, False)

    def held(self, action: str) -> bool:
        return self._current.get(action, False)

    def movement(self) -> pygame.Vector2:
        return self._move.copy()

    @property
    def move_x(self) -> float:
        return self._move.x

    @property
    def move_y(self) -> float:
        return self._move.y

    def consume_presses(self) -> None:
        """Prevent a menu-confirm press from also firing inside the new scene."""
        self._pressed = {name: False for name in self._pressed}

    def rumble(self, low: float, high: float, duration_ms: int) -> None:
        if not self.connected:
            return
        try:
            self.controller.rumble(low, high, duration_ms)
        except (pygame.error, AttributeError):
            pass
