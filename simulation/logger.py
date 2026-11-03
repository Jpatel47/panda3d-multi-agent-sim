"""Record a simulation run as a JSON episode file."""
import copy
import json
import os

# Bump when the layout of the episode file changes.
# 2: per-frame "collisions" and metadata "collision_count".
SCHEMA_VERSION = 2

# Panda3D stores positions as 32-bit floats, which hold about 7 significant
# digits. Six decimal places keeps that precision at this world scale
# without writing float noise like 12.345678329467773.
DECIMALS = 6


def _rounded(values):
    return [round(v, DECIMALS) for v in values]


def agent_state(agent):
    """The per-step record of one agent."""
    return {
        "id": agent.agent_id,
        "behavior": agent.behavior.name if agent.behavior else None,
        "position": _rounded(agent.position),
        "velocity": _rounded((agent.velocity.x, agent.velocity.y)),
        # Rounding can turn 359.9999999 into 360.0; keep it in [0, 360).
        "heading": round(agent.heading, DECIMALS) % 360.0,
    }


class EpisodeLogger:
    """
    Collects one frame per simulation step and writes them as one JSON file.

    Frame k holds the state after k steps, so frame 0 is the spawn state and
    an episode of N steps has N + 1 frames. The metadata embeds a copy of
    the full config, so the file alone is enough to reproduce the run.
    """

    def __init__(self, cfg, dt):
        self.metadata = {
            "seed": cfg["simulation"]["seed"],
            "behavior": cfg["agents"]["behavior"],
            "agent_count": cfg["agents"]["count"],
            "dt": dt,
            "steps": 0,
            "collision_count": 0,
            "config": copy.deepcopy(cfg),
        }
        self.frames = []

    def record(self, sim):
        """Append the current state of every agent in `sim`."""
        self.frames.append({
            "step": sim.steps,
            "time": round(sim.time, DECIMALS),
            "agents": [agent_state(agent) for agent in sim.agents],
            # Id pairs that touched during this step, after which they were
            # pushed apart. Empty for frame 0.
            "collisions": [list(pair) for pair in sim.last_collisions],
        })
        self.metadata["steps"] = sim.steps
        self.metadata["collision_count"] = sim.collision_count

    def to_dict(self):
        return {
            "schema_version": SCHEMA_VERSION,
            "metadata": self.metadata,
            "frames": self.frames,
        }

    def write(self, path):
        """Write the episode to `path`, creating its directory if needed."""
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(path, "w") as f:
            # Compact separators: an episode holds one record per agent per
            # step, and the indentation would dominate the file size.
            json.dump(self.to_dict(), f, separators=(",", ":"))
            f.write("\n")
        return path
