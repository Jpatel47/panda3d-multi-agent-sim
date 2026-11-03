from panda3d.core import LPoint3f, LVector3f

from behaviors.base import Behavior


class SeekTarget(Behavior):
    """
    Head straight for a random target point inside the world; once within
    `arrive_radius` of it, pick a new one.

    On the last step before arriving the agent slows down so it stops on the
    target instead of overshooting it, which keeps the behavior stable even
    with large time steps.
    """

    name = "seek_target"

    def __init__(self, rng, arrive_radius=1.0):
        super().__init__(rng)
        if arrive_radius <= 0:
            raise ValueError("arrive_radius must be positive")
        self.arrive_radius = arrive_radius
        self.target = None
        self.targets_reached = 0

    @classmethod
    def from_config(cls, rng, cfg):
        params = cfg["behaviors"][cls.name]
        return cls(rng, arrive_radius=params["arrive_radius"])

    def _new_target(self, agent):
        # agent.bound is how far from the origin the agent can move, so every
        # target is reachable.
        return LPoint3f(self.rng.uniform(-agent.bound, agent.bound),
                        self.rng.uniform(-agent.bound, agent.bound),
                        0.0)

    def _offset(self, agent):
        offset = self.target - agent.position
        offset.z = 0.0
        return offset

    def on_collision(self, agent, normal):
        # Another agent is in the way: give up on this target and pick a new
        # one, instead of pushing into the other agent on every step.
        self.target = self._new_target(agent)

    def decide(self, agent, dt):
        if self.target is None:
            self.target = self._new_target(agent)

        offset = self._offset(agent)
        if offset.length() <= self.arrive_radius:
            self.targets_reached += 1
            self.target = self._new_target(agent)
            offset = self._offset(agent)

        distance = offset.length()
        if distance == 0.0:
            return LVector3f(0.0, 0.0, 0.0)

        max_step = agent.speed * dt
        throttle = 1.0 if max_step <= distance else distance / max_step
        return offset * (throttle / distance)
