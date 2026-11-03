import math

from panda3d.core import LVector3f

from behaviors.base import Behavior


class RandomWalk(Behavior):
    """
    Move in a random direction at full speed and pick a new direction every
    `change_interval` seconds of simulated time.

    Turning is driven by elapsed time rather than a frame counter, so the
    walk looks the same at 30 FPS and at 240 FPS.
    """

    name = "random_walk"

    def __init__(self, rng, change_interval=1.0):
        super().__init__(rng)
        if change_interval <= 0:
            raise ValueError("change_interval must be positive")
        self.change_interval = change_interval
        self._direction = self._new_direction()
        self._elapsed = 0.0

    @classmethod
    def from_config(cls, rng, cfg):
        params = cfg["behaviors"][cls.name]
        return cls(rng, change_interval=params["change_interval"])

    def _new_direction(self):
        # Uniform over all headings (normalising a random point in a square
        # would favour the diagonals).
        angle = self.rng.uniform(0.0, 2.0 * math.pi)
        return LVector3f(math.cos(angle), math.sin(angle), 0.0)

    def on_collision(self, agent, normal):
        # Bounce: if the walk points into the other agent, mirror it off the
        # contact normal so the next steps lead away from it.
        along = self._direction.dot(normal)
        if along < 0.0:
            self._direction = self._direction - normal * (2.0 * along)

    def decide(self, agent, dt):
        self._elapsed += dt
        if self._elapsed >= self.change_interval:
            # Keep the remainder so turns stay on a fixed time grid; a frame
            # longer than the interval still produces a single turn.
            self._elapsed %= self.change_interval
            self._direction = self._new_direction()
        return LVector3f(self._direction)
