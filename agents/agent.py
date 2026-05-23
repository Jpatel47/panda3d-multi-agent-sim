from panda3d.core import LPoint3f, LVector3f, LODNode, NodePath
import random


class Agent:

    def __init__(self, world, agent_id, config):
        self.world = world
        self.agent_id = agent_id
        self.cfg = config

        self.state = {
            "position": LPoint3f(
                random.uniform(-20, 20),
                random.uniform(-20, 20),
                0.5
            ),
            "velocity": LVector3f(0, 0, 0),
            "reward": 0.0,
            "step": 0
        }

        self.behavior = None
        self._setup_node()

    def _setup_node(self):
        size = self.cfg["size"]
        color = self.cfg["color"]

        lod = LODNode(f"agent_{self.agent_id}_lod")
        self.lod_node = self.world.render.attachNewNode(lod)
        self.lod_node.setPos(self.state["position"])

        high = self.world.loader.loadModel("models/misc/sphere")
        high.setScale(size)
        high.setColor(color[0], color[1], color[2], color[3])
        high.reparentTo(self.lod_node)
        lod.addSwitch(self.world.cfg["lod"]["near"], 0)

        low = self.world.loader.loadModel("models/misc/sphere")
        low.setScale(size * 0.5)
        low.setColor(color[0], color[1], color[2] + 0.3, color[3])
        low.reparentTo(self.lod_node)
        lod.addSwitch(self.world.cfg["lod"]["far"],
                      self.world.cfg["lod"]["near"])

    def set_behavior(self, behavior):
        self.behavior = behavior

    def update(self, dt):
        if self.behavior is None:
            return

        action = self.behavior.decide(self.state)
        self.state["velocity"] = action * self.cfg["speed"]

        new_pos = self.state["position"] + self.state["velocity"] * dt
        half = self.world.cfg["world"]["size"] / 2 - 1
        new_pos.x = max(-half, min(half, new_pos.x))
        new_pos.y = max(-half, min(half, new_pos.y))
        new_pos.z = 0.5

        self.state["position"] = new_pos
        self.lod_node.setPos(new_pos)
        self.state["step"] += 1
