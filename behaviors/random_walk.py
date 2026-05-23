from panda3d.core import LVector3f
import random


class RandomWalk:
    """
    Pluggable behavior: agent moves in a random direction,
    changing direction every 60 steps.
    """

    def __init__(self):
        self._direction = self._new_direction()
        self._steps = 0

    def _new_direction(self):
        x = random.uniform(-1, 1)
        y = random.uniform(-1, 1)
        v = LVector3f(x, y, 0)
        v.normalize()
        return v

    def decide(self, state):
        self._steps += 1
        if self._steps % 60 == 0:
            self._direction = self._new_direction()
        return self._direction
