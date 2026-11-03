"""Simulation core: builds the agents and steps them. Needs no window."""
import random

from panda3d.core import NodePath, RenderState, TransformState

from agents.agent import Agent
from behaviors.registry import create_behavior


class Simulation:
    """
    Owns the agents and advances them by a time step.

    All randomness comes from cfg["simulation"]["seed"]: two simulations
    built from the same config and stepped with the same dt values produce
    identical trajectories.

    Agents live under `root`, a plain scene-graph node. The viewer parents
    it under ShowBase.render to draw it; without a viewer nothing renders.
    """

    def __init__(self, cfg):
        self.cfg = cfg
        self.seed = cfg["simulation"]["seed"]
        self.behavior_name = cfg["agents"]["behavior"]
        self.root = NodePath("simulation")
        self.time = 0.0
        self.steps = 0

        master = random.Random(self.seed)
        self.agents = []
        for agent_id in range(cfg["agents"]["count"]):
            # Each agent gets its own random stream, drawn in id order, so
            # agent N's spawn point and choices only depend on the seed and N.
            rng = random.Random(master.getrandbits(64))
            agent = Agent(agent_id, cfg, self.root, rng)
            agent.set_behavior(create_behavior(self.behavior_name, rng, cfg))
            self.agents.append(agent)

    def step(self, dt):
        """Advance every agent by dt seconds of simulated time."""
        for agent in self.agents:
            agent.update(dt)
        self.steps += 1
        self.time += dt

        # Every setPos creates a new TransformState, and Panda3D keeps the
        # ones nothing references any more in a cache until garbageCollect()
        # is called. ShowBase calls it once per frame; without a ShowBase
        # (headless runs) the cache would grow by one state per agent per
        # step and slow every later step down, so the core does it itself.
        TransformState.garbageCollect()
        RenderState.garbageCollect()
