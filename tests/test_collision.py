"""Agent-agent collisions: detection, separation, bounce and episode counts."""
import math
import random

import pytest
from panda3d.core import LPoint3f, LVector3f, NodePath

from agents.agent import Agent
from behaviors.random_walk import RandomWalk
from behaviors.seek_target import SeekTarget
from helpers import Fixed
from simulation.core import Simulation
from simulation.headless import run_headless


def _pair(cfg, a_x, b_x, a_dir, b_dir):
    """Two agents on the x axis, each walking in a fixed direction."""
    cfg["agents"]["count"] = 2
    sim = Simulation(cfg)
    a, b = sim.agents
    a.place(a_x, 0.0)
    b.place(b_x, 0.0)
    a.set_behavior(Fixed(a_dir))
    b.set_behavior(Fixed(b_dir))
    return sim, a, b


def _distance(a, b):
    return math.hypot(a.position.x - b.position.x,
                      a.position.y - b.position.y)


def _crowd(cfg, behavior="random_walk", steps=200):
    """Many agents packed into a small area, so they keep bumping."""
    cfg["agents"].update(count=30, spawn_range=6.0, behavior=behavior)
    cfg["simulation"].update(steps=steps, dt=0.05)
    return run_headless(cfg)


def test_every_agent_gets_a_collision_sphere_of_its_radius(cfg):
    sim = Simulation(cfg)
    for agent in sim.agents:
        collider = agent.node.find("+CollisionNode")
        assert not collider.isEmpty()
        sphere = collider.node().getSolid(0)
        assert sphere.getRadius() == pytest.approx(agent.radius)


def test_head_on_collision_is_detected_separated_and_bounced(cfg):
    # 8 units/s * 0.1 s: the 6-unit gap closes by 1.6 per step, so the two
    # radius-1 spheres first touch on step 3 (centres 1.2 apart).
    sim, a, b = _pair(cfg, -3.0, 3.0, (1, 0, 0), (-1, 0, 0))

    sim.step(0.1)
    sim.step(0.1)
    assert sim.last_collisions == []
    assert _distance(a, b) == pytest.approx(2.8)

    sim.step(0.1)
    assert sim.last_collisions == [(0, 1)]
    assert sim.collision_count == 1
    # Each was pushed back by half of the 0.8 overlap...
    assert _distance(a, b) == pytest.approx(a.radius + b.radius)
    assert a.position.x == pytest.approx(-1.0)
    assert b.position.x == pytest.approx(1.0)
    # ...and their velocities were mirrored away from each other.
    assert a.velocity == LVector3f(-cfg["agents"]["speed"], 0, 0)
    assert b.velocity == LVector3f(cfg["agents"]["speed"], 0, 0)
    assert a.heading == pytest.approx(180.0)
    assert b.heading == pytest.approx(0.0)


def test_agents_moving_apart_keep_their_velocity(cfg):
    # b sits inside a's sphere but walks away from it: they are separated,
    # and b's velocity, which already points away from a, is left alone.
    sim, a, b = _pair(cfg, 0.0, 1.0, (0, 0, 0), (1, 0, 0))
    sim.step(0.01)
    assert sim.last_collisions == [(0, 1)]
    assert b.velocity == LVector3f(cfg["agents"]["speed"], 0, 0)
    assert _distance(a, b) == pytest.approx(2.0)


def test_agents_far_apart_never_collide(cfg):
    sim, a, b = _pair(cfg, -10.0, 10.0, (0, 1, 0), (0, -1, 0))
    for _ in range(50):
        sim.step(0.1)
    assert sim.collision_count == 0


def test_agents_on_the_same_spot_are_still_separated(cfg):
    sim, a, b = _pair(cfg, 5.0, 5.0, (0, 0, 0), (0, 0, 0))
    sim.step(0.1)
    assert sim.last_collisions == [(0, 1)]
    assert _distance(a, b) == pytest.approx(2.0)


def test_random_walk_turns_away_from_the_other_agent():
    walk = RandomWalk(random.Random(0), change_interval=1.0)
    direction = walk.decide(None, 0.0)
    away = tuple(-direction)

    walk.on_collision(None, -direction)       # walked straight into it
    assert tuple(walk.decide(None, 0.0)) == pytest.approx(away)

    walk.on_collision(None, -direction)       # already walking away
    assert tuple(walk.decide(None, 0.0)) == pytest.approx(away)


def test_seek_target_picks_a_new_target_when_blocked(cfg):
    rng = random.Random(0)
    agent = Agent(0, cfg, NodePath("root"), rng)
    seek = SeekTarget(rng)
    agent.set_behavior(seek)
    agent.update(0.1)
    blocked = LPoint3f(seek.target)

    agent.bounce(LVector3f(1, 0, 0), 0.0)
    assert seek.target != blocked


@pytest.mark.parametrize("behavior", ["random_walk", "seek_target"])
def test_crowded_episode_logs_collisions(cfg, behavior):
    episode = _crowd(cfg, behavior)
    total = episode.metadata["collision_count"]
    assert total > 0
    assert total == sum(len(frame["collisions"]) for frame in episode.frames)
    assert episode.frames[0]["collisions"] == []
    for frame in episode.frames:
        for a, b in frame["collisions"]:
            assert 0 <= a < b < 30


def test_crowded_episodes_are_still_reproducible(cfg):
    assert _crowd(cfg).to_dict() == _crowd(cfg).to_dict()


def test_collisions_can_be_disabled(cfg):
    cfg["collisions"]["enabled"] = False
    episode = _crowd(cfg)
    assert episode.metadata["collision_count"] == 0
    assert all(frame["collisions"] == [] for frame in episode.frames)

    sim = Simulation(cfg)
    assert sim.collisions is None
    assert sim.agents[0].node.find("+CollisionNode").isEmpty()
