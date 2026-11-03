"""Simulation core and viewer: config-driven setup and reproducible runs."""
import pytest
import yaml
from panda3d.core import TransformState

from behaviors.seek_target import SeekTarget
from simulation.config import load_config
from simulation.core import Simulation


def _trajectory(cfg, steps=200, dt=1 / 60):
    sim = Simulation(cfg)
    frames = []
    for _ in range(steps):
        sim.step(dt)
        frames.append([tuple(agent.position) for agent in sim.agents])
    return frames


@pytest.mark.parametrize("behavior", ["random_walk", "seek_target"])
def test_same_seed_reproduces_the_run(cfg, behavior):
    cfg["agents"]["behavior"] = behavior
    assert _trajectory(cfg) == _trajectory(cfg)


def test_different_seed_gives_a_different_run(cfg):
    first = _trajectory(cfg)
    cfg["simulation"]["seed"] += 1
    assert _trajectory(cfg) != first


def test_agents_and_behavior_come_from_config(cfg):
    cfg["agents"]["count"] = 7
    cfg["agents"]["behavior"] = "seek_target"
    sim = Simulation(cfg)

    assert [agent.agent_id for agent in sim.agents] == list(range(7))
    assert all(type(agent.behavior) is SeekTarget for agent in sim.agents)
    # Every agent has its own behavior instance and its own random stream.
    assert len({id(agent.behavior) for agent in sim.agents}) == 7
    assert len({id(agent.behavior.rng) for agent in sim.agents}) == 7
    assert sim.root.getNumChildren() == 7


def test_step_advances_every_agent_and_the_clock(cfg):
    sim = Simulation(cfg)
    for _ in range(10):
        sim.step(0.1)
    assert sim.steps == 10
    assert sim.time == pytest.approx(1.0)
    assert all(agent.steps == 10 for agent in sim.agents)


def test_stepping_without_showbase_does_not_pile_up_transform_states(cfg):
    # Regression: every setPos creates a TransformState, and Panda3D keeps
    # unreferenced ones cached until TransformState.garbageCollect() runs.
    # Only ShowBase ran it (once per frame), so headless runs cached one
    # more state per agent per step and got slower as the cache grew.
    sim = Simulation(cfg)
    TransformState.garbageCollect()
    before = TransformState.getNumStates()
    for _ in range(1000):
        sim.step(0.05)
    assert TransformState.getNumStates() - before < 100


def test_missing_seed_is_replaced_with_a_concrete_one(cfg, tmp_path):
    cfg["simulation"]["seed"] = None
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(cfg))

    seed = load_config(path)["simulation"]["seed"]
    assert isinstance(seed, int) and seed >= 0


def test_viewer_builds_and_steps_without_a_window(cfg):
    # conftest.py sets window-type none, so ShowBase opens no window.
    from simulation.world import SimulationWorld

    sim = Simulation(cfg)
    world = SimulationWorld(cfg, sim)
    try:
        for _ in range(3):
            world.taskMgr.step()
        assert sim.steps == 3
        assert sim.root.getParent() == world.render
        assert all(not agent.node.find("+LODNode").isEmpty()
                   for agent in sim.agents)
    finally:
        world.destroy()
