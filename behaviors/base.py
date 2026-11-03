"""Interface shared by every agent behavior."""
from abc import ABC, abstractmethod


class Behavior(ABC):
    """
    Decides which way an agent wants to move on each simulation step.

    Each behavior gets its own seeded random.Random, so a whole run can be
    reproduced from simulation.seed in config.yaml.
    """

    #: Key used for this behavior in config.yaml and in the registry.
    name = None

    def __init__(self, rng):
        self.rng = rng

    @classmethod
    def from_config(cls, rng, cfg):
        """Build the behavior from the full config dict.

        Behaviors with tuneable parameters override this and read them from
        cfg["behaviors"][cls.name].
        """
        return cls(rng)

    @abstractmethod
    def decide(self, agent, dt):
        """Return the desired move direction for this step.

        The result is an LVector3f on the ground plane (z is ignored). Its
        length is the fraction of the agent's top speed to use: 1.0 is full
        speed, 0.0 is standing still. Longer vectors are clamped to 1.0.
        """
