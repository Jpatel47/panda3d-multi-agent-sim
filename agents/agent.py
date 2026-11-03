import math

from panda3d.core import LPoint3f, LVector3f


class Agent:
    """
    A point agent that moves on the ground plane.

    Each update it asks its behavior for a direction, moves at up to
    agents.speed units per second, and is clamped so its sphere stays inside
    the world square. `node` is a scene-graph node that follows the agent's
    position; the viewer attaches the visible model to it.
    """

    def __init__(self, agent_id, cfg, parent, rng):
        agents_cfg = cfg["agents"]
        self.agent_id = agent_id
        self.speed = agents_cfg["speed"]
        self.radius = agents_cfg["size"]
        # Furthest the centre can get from the origin on x or y.
        self.bound = cfg["world"]["size"] / 2 - self.radius

        spawn = min(agents_cfg["spawn_range"], self.bound)
        self.position = LPoint3f(rng.uniform(-spawn, spawn),
                                 rng.uniform(-spawn, spawn),
                                 self.radius)
        self.velocity = LVector3f(0.0, 0.0, 0.0)
        # Direction of travel in degrees, counter-clockwise from +X.
        self.heading = 0.0
        self.steps = 0
        self.behavior = None

        self.node = parent.attachNewNode(f"agent_{agent_id}")
        self.node.setPos(self.position)

    def set_behavior(self, behavior):
        self.behavior = behavior

    def update(self, dt):
        if self.behavior is None:
            return

        decided = self.behavior.decide(self, dt)
        direction = LVector3f(decided.x, decided.y, 0.0)
        if direction.lengthSquared() > 1.0:
            direction.normalize()
        self.velocity = direction * self.speed

        new_pos = self.position + self.velocity * dt
        new_pos.x = max(-self.bound, min(self.bound, new_pos.x))
        new_pos.y = max(-self.bound, min(self.bound, new_pos.y))
        new_pos.z = self.radius
        self.position = new_pos

        if self.velocity.lengthSquared() > 0.0:
            self.heading = math.degrees(
                math.atan2(self.velocity.y, self.velocity.x)) % 360.0

        self.node.setPos(self.position)
        self.steps += 1
