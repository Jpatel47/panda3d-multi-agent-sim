"""Agent-agent collision detection with Panda3D, and a simple bounce."""
from panda3d.core import (
    BitMask32, CollisionHandlerQueue, CollisionNode, CollisionSphere,
    CollisionTraverser, LVector3f,
)

# Agents only collide with agents. The world edge is handled by clamping.
AGENT_MASK = BitMask32.bit(1)


class CollisionSystem:
    """
    Finds touching agents with a CollisionTraverser and pushes them apart.

    Every agent gets a CollisionSphere of its radius under its node. Each
    sphere is both a "from" and an "into" object, so a touching pair shows
    up twice in the CollisionHandlerQueue (A into B and B into A); step()
    reports each pair once.
    """

    def __init__(self, agents, root):
        self.root = root
        self.agents = {agent.agent_id: agent for agent in agents}
        self.traverser = CollisionTraverser("agent_collisions")
        self.queue = CollisionHandlerQueue()

        for agent in agents:
            node = CollisionNode(f"agent_{agent.agent_id}_collider")
            node.addSolid(CollisionSphere(0, 0, 0, agent.radius))
            node.setFromCollideMask(AGENT_MASK)
            node.setIntoCollideMask(AGENT_MASK)
            collider = agent.node.attachNewNode(node)
            collider.setPythonTag("agent", agent)
            self.traverser.addCollider(collider, self.queue)

    def detect(self):
        """Return the sorted (a, b) id pairs of touching agents, a < b."""
        self.traverser.traverse(self.root)
        pairs = set()
        for entry in self.queue.getEntries():
            a = entry.getFromNodePath().getPythonTag("agent").agent_id
            b = entry.getIntoNodePath().getPythonTag("agent").agent_id
            pairs.add((min(a, b), max(a, b)))
        return sorted(pairs)

    def resolve(self, pairs):
        """Separate each pair along the line between them and bounce both.

        Pairs are handled one at a time in id order, so the result is
        deterministic. Pushing one pair apart can make another pair touch;
        that is picked up on the next step.
        """
        for a_id, b_id in pairs:
            a, b = self.agents[a_id], self.agents[b_id]
            offset = b.position - a.position
            offset.z = 0.0
            distance = offset.length()
            if distance > 1e-6:
                normal = offset / distance      # unit vector from a to b
            else:
                normal = LVector3f(1.0, 0.0, 0.0)  # same spot: any axis works
            overlap = max(0.0, a.radius + b.radius - distance)
            a.bounce(-normal, overlap / 2.0)
            b.bounce(normal, overlap / 2.0)

    def step(self):
        """Detect and resolve the collisions of this step; return the pairs."""
        pairs = self.detect()
        self.resolve(pairs)
        return pairs
