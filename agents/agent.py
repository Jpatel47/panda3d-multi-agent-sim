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

    def place(self, x, y):
        """Move to (x, y), clamped to the world, on the ground plane."""
        self.position = LPoint3f(max(-self.bound, min(self.bound, x)),
                                 max(-self.bound, min(self.bound, y)),
                                 self.radius)
        self.node.setPos(self.position)

    def _update_heading(self):
        # Standing still keeps the previous heading.
        if self.velocity.lengthSquared() > 0.0:
            self.heading = math.degrees(
                math.atan2(self.velocity.y, self.velocity.x)) % 360.0

    def update(self, dt):
        if self.behavior is None:
            return

        decided = self.behavior.decide(self, dt)
        direction = LVector3f(decided.x, decided.y, 0.0)
        if direction.lengthSquared() > 1.0:
            direction.normalize()
        self.velocity = direction * self.speed

        new_pos = self.position + self.velocity * dt
        self.place(new_pos.x, new_pos.y)
        self._update_heading()
        self.steps += 1

    def bounce(self, normal, distance):
        """
        Respond to touching another agent.

        `normal` is a unit vector on the ground plane pointing from the
        other agent towards this one. The agent is pushed `distance` along
        it and, if it was moving towards the other agent, its velocity is
        mirrored off the normal. The behavior is told last, so it can
        change what it does on the next step.
        """
        pushed = self.position + normal * distance
        self.place(pushed.x, pushed.y)

        along = self.velocity.dot(normal)
        if along < 0.0:
            self.velocity = self.velocity - normal * (2.0 * along)
            self._update_heading()

        if self.behavior is not None:
            self.behavior.on_collision(self, normal)
