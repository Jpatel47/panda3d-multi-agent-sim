"""RandomWalk: frame-rate independent turning and seeded randomness."""
import random

import pytest
from panda3d.core import NodePath

from agents.agent import Agent
from behaviors.random_walk import RandomWalk


def _walker(cfg, seed=0):
    rng = random.Random(seed)
    agent = Agent(0, cfg, NodePath("root"), rng)
    agent.set_behavior(RandomWalk(rng, change_interval=1.0))
    return agent


def _count_turns(agent, fps, seconds):
    dt = 1.0 / fps
    turns, previous = 0, None
    for _ in range(round(seconds * fps)):
        agent.update(dt)
        direction = (agent.velocity.x, agent.velocity.y)
        if previous is not None and direction != previous:
            turns += 1
        previous = direction
    return turns


def test_turn_rate_does_not_depend_on_frame_rate(cfg):
    # Regression: turns used to happen every 60 frames, i.e. once in 2.5 s
    # at 30 FPS but ten times at 240 FPS.
    assert _count_turns(_walker(cfg), fps=30, seconds=2.5) == 2
    assert _count_turns(_walker(cfg), fps=240, seconds=2.5) == 2


def test_a_long_frame_turns_once_and_keeps_the_remainder():
    walk = RandomWalk(random.Random(1), change_interval=1.0)
    first = walk.decide(None, 0.1)
    after_hitch = walk.decide(None, 3.5)   # elapsed 3.6 -> turn, 0.6 left
    assert after_hitch != first
    assert walk.decide(None, 0.3) == after_hitch   # 0.9 < 1.0, no turn
    assert walk.decide(None, 0.1) != after_hitch   # 1.0, turn


def test_directions_are_unit_vectors_on_the_ground_plane():
    walk = RandomWalk(random.Random(3), change_interval=0.5)
    for _ in range(50):
        direction = walk.decide(None, 0.5)
        assert direction.z == 0.0
        assert direction.length() == pytest.approx(1.0, abs=1e-6)


def test_seed_determines_the_walk():
    def directions(seed):
        walk = RandomWalk(random.Random(seed), change_interval=0.25)
        return [tuple(walk.decide(None, 0.25)) for _ in range(20)]

    assert directions(7) == directions(7)
    assert directions(7) != directions(8)


def test_rejects_non_positive_interval():
    with pytest.raises(ValueError):
        RandomWalk(random.Random(0), change_interval=0)
