"""SeekTarget: reaches its target without overshooting, then picks another."""
import math
import random

from panda3d.core import LPoint3f, NodePath

from agents.agent import Agent
from behaviors.seek_target import SeekTarget


def _seeker(cfg, arrive_radius=1.0, seed=0):
    rng = random.Random(seed)
    agent = Agent(0, cfg, NodePath("root"), rng)
    seek = SeekTarget(rng, arrive_radius=arrive_radius)
    agent.set_behavior(seek)
    return agent, seek


def _xy_distance(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


def test_closes_in_on_the_target_then_picks_a_new_one(cfg):
    agent, seek = _seeker(cfg)
    agent.update(0.05)                      # first decide picks a target
    target = LPoint3f(seek.target)

    distances = [_xy_distance(target, agent.position)]
    for _ in range(2000):
        agent.update(0.05)
        if seek.targets_reached:
            break
        distances.append(_xy_distance(target, agent.position))

    assert seek.targets_reached == 1
    assert seek.target != target
    assert all(b < a for a, b in zip(distances, distances[1:]))


def test_large_time_steps_do_not_overshoot(cfg):
    # 8 units/s * 2 s = 16 units per step, far more than the arrive radius;
    # without slowing down on the last step the agent would jump past the
    # target forever.
    agent, seek = _seeker(cfg, arrive_radius=0.5)
    for _ in range(30):
        agent.update(2.0)
    assert seek.targets_reached >= 2


def test_targets_are_inside_the_movement_bounds(cfg):
    agent, seek = _seeker(cfg)
    targets = set()
    for _ in range(500):
        agent.update(1.0)
        targets.add((seek.target.x, seek.target.y))
    assert len(targets) > 10
    assert all(abs(x) <= agent.bound and abs(y) <= agent.bound
               for x, y in targets)
