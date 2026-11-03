from panda3d.core import LVector3f
import random


class RandomWalk:
    """
    Pluggable behavior: agent moves in a random direction and picks a new
    one every `change_interval` seconds of simulated time.

    Turning is driven by elapsed time rather than a frame counter, so the
    walk looks the same at 30 FPS and at 240 FPS.
    """

    def __init__(self, change_interval=1.0):
        self.change_interval = change_interval
        self._direction = self._new_direction()
        self._elapsed = 0.0

    def _new_direction(self):
        x = random.uniform(-1, 1)
        y = random.uniform(-1, 1)
        v = LVector3f(x, y, 0)
        v.normalize()
        return v

    def decide(self, state, dt):
        self._elapsed += dt
        if self._elapsed >= self.change_interval:
            # Keep the remainder so turns stay on a fixed time grid; a frame
            # longer than the interval still produces a single turn.
            self._elapsed %= self.change_interval
            self._direction = self._new_direction()
        return self._direction
