"""Run the simulation without a window, with a fixed time step."""
import os

from simulation.core import Simulation
from simulation.logger import EpisodeLogger


def episode_path(cfg):
    """Where the episode for this config is written.

    The name depends only on the behavior and the seed, so re-running the
    same configuration overwrites its previous file instead of piling up
    copies.
    """
    name = f"episode_{cfg['agents']['behavior']}_seed{cfg['simulation']['seed']}.json"
    return os.path.join(cfg["simulation"]["export_path"], name)


def run_headless(cfg):
    """Step a new Simulation simulation.steps times by simulation.dt.

    Nothing is rendered and no window or ShowBase is created. Every step is
    recorded, and the EpisodeLogger holding the run is returned.
    """
    steps = cfg["simulation"]["steps"]
    dt = cfg["simulation"]["dt"]
    if not isinstance(steps, int) or steps < 1:
        raise ValueError(f"simulation.steps must be a positive integer, got {steps!r}")
    if dt <= 0:
        raise ValueError(f"simulation.dt must be positive, got {dt!r}")

    sim = Simulation(cfg)
    episode = EpisodeLogger(cfg, dt)
    episode.record(sim)
    for _ in range(steps):
        sim.step(dt)
        episode.record(sim)
    return episode
