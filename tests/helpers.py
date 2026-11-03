"""Helpers shared by the test modules."""
from panda3d.core import LVector3f

from behaviors.base import Behavior


class Fixed(Behavior):
    """Test behavior that always asks for the same direction."""

    name = "fixed"

    def __init__(self, direction):
        super().__init__(rng=None)
        self.direction = LVector3f(*direction)

    def decide(self, agent, dt):
        return LVector3f(self.direction)
