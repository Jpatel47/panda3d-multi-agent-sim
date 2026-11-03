"""Agent: seeded spawns, speed, heading and staying inside the world."""
import math
import random

import pytest
from panda3d.core import LPoint3f, LVector3f, NodePath

from agents.agent import Agent
from behaviors.base import Behavior


class Fixed(Behavior):
    """Test behavior that always asks for the same direction."""

    name = "fixed"

    def __init__(self, direction):
        super().__init__(rng=None)
        self.direction = LVector3f(*direction)

    def decide(self, agent, dt):
        return LVector3f(self.direction)


def _agent(cfg, direction=None, seed=0):
    agent = Agent(0, cfg, NodePath("root"), random.Random(seed))
    if direction is not None:
        agent.set_behavior(Fixed(direction))
    return agent


def test_spawns_on_the_ground_inside_the_spawn_range(cfg):
    spawn = cfg["agents"]["spawn_range"]
    for seed in range(50):
        agent = _agent(cfg, seed=seed)
        assert abs(agent.position.x) <= spawn
        assert abs(agent.position.y) <= spawn
        assert agent.position.z == cfg["agents"]["size"]
        assert agent.node.getPos() == agent.position


def test_spawn_range_is_capped_at_the_world_edge(cfg):
    cfg["agents"]["spawn_range"] = 1000.0
    for seed in range(50):
        agent = _agent(cfg, seed=seed)
        assert abs(agent.position.x) <= agent.bound
        assert abs(agent.position.y) <= agent.bound


def test_spawn_point_depends_only_on_the_seed(cfg):
    assert _agent(cfg, seed=5).position == _agent(cfg, seed=5).position
    assert _agent(cfg, seed=5).position != _agent(cfg, seed=6).position


def test_moves_at_top_speed_in_the_requested_direction(cfg):
    agent = _agent(cfg, direction=(0, 1, 0))
    start = LPoint3f(agent.position)
    speed = cfg["agents"]["speed"]

    agent.update(0.5)

    assert agent.velocity == LVector3f(0, speed, 0)
    assert agent.position.x == pytest.approx(start.x)
    assert agent.position.y == pytest.approx(start.y + speed * 0.5)
    assert agent.heading == pytest.approx(90.0)
    assert agent.node.getPos() == agent.position
    assert agent.steps == 1


def test_longer_directions_are_capped_at_top_speed(cfg):
    agent = _agent(cfg, direction=(3, 4, 0))
    agent.update(0.1)
    assert agent.velocity.length() == pytest.approx(cfg["agents"]["speed"])
    assert agent.heading == pytest.approx(math.degrees(math.atan2(4, 3)))


def test_shorter_directions_move_at_a_fraction_of_top_speed(cfg):
    agent = _agent(cfg, direction=(-0.25, 0, 0))
    agent.update(0.1)
    assert agent.velocity.length() == pytest.approx(
        0.25 * cfg["agents"]["speed"])
    assert agent.heading == pytest.approx(180.0)


def test_vertical_component_is_ignored(cfg):
    agent = _agent(cfg, direction=(0, 0, 1))
    start = LPoint3f(agent.position)
    agent.update(1.0)
    assert agent.velocity == LVector3f(0, 0, 0)
    assert agent.position == start


def test_stays_inside_the_world(cfg):
    agent = _agent(cfg, direction=(1, -1, 0))
    for _ in range(100):
        agent.update(1.0)
    assert agent.bound == cfg["world"]["size"] / 2 - cfg["agents"]["size"]
    assert agent.position.x == pytest.approx(agent.bound)
    assert agent.position.y == pytest.approx(-agent.bound)


def test_heading_is_kept_while_standing_still(cfg):
    agent = _agent(cfg, direction=(0, -1, 0))
    agent.update(0.1)
    assert agent.heading == pytest.approx(270.0)

    agent.behavior.direction = LVector3f(0, 0, 0)
    agent.update(0.1)
    assert agent.velocity.length() == 0.0
    assert agent.heading == pytest.approx(270.0)


def test_without_a_behavior_the_agent_stays_put(cfg):
    agent = _agent(cfg)
    start = LPoint3f(agent.position)
    agent.update(1.0)
    assert agent.position == start
    assert agent.steps == 0
