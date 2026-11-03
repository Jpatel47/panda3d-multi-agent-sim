"""Regression test: RandomWalk's turn rate must not depend on frame rate."""
from types import SimpleNamespace

from panda3d.core import NodePath

from agents.agent import Agent
from behaviors.random_walk import RandomWalk

CFG = {
    "world": {"size": 100},
    "agents": {"count": 1, "speed": 8.0, "size": 1.0,
               "color": [0.8, 0.2, 0.2, 1.0]},
    "lod": {"near": 30.0, "far": 80.0},
}


class _NullLoader:
    """Stands in for ShowBase.loader; returns empty nodes instead of models."""

    def loadModel(self, path):
        return NodePath(path)


def _count_turns(fps, seconds):
    world = SimpleNamespace(render=NodePath("render"), loader=_NullLoader(),
                            cfg=CFG)
    agent = Agent(world, 0, CFG["agents"])
    agent.set_behavior(RandomWalk())

    dt = 1.0 / fps
    turns, previous = 0, None
    for _ in range(round(seconds * fps)):
        agent.update(dt)
        velocity = agent.state["velocity"]
        direction = (velocity.x, velocity.y)
        if previous is not None and direction != previous:
            turns += 1
        previous = direction
    return turns


def test_turn_rate_does_not_depend_on_frame_rate():
    # 2.5 s of simulated time with the default 1 s interval means two turns,
    # whether the simulation is stepped at 30 FPS or at 240 FPS.
    assert _count_turns(fps=30, seconds=2.5) == 2
    assert _count_turns(fps=240, seconds=2.5) == 2
