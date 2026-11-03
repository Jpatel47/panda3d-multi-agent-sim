# panda3d-multi-agent-sim

A small multi-agent simulation written in Python on top of
[Panda3D](https://www.panda3d.org/). Agents move around a square ground
plane, each driven by a pluggable behavior that `config.yaml` selects.
Agents that touch are detected with Panda3D's collision system and
bounced apart. Every run can be reproduced from one seed. The simulation
core needs no window. It can run headless with a fixed time step and
export each run as a JSON episode file, and the whole thing is
unit-tested headless. A Panda3D viewer draws the agents as two-level LOD
spheres.

## Setup

Python 3.9 or newer. CI runs the tests on Python 3.9, 3.11 and 3.13.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt        # Panda3D 1.10.16, PyYAML 6.0.3
pip install -r requirements-dev.txt    # adds pytest, for the tests
```

## Running

```bash
python main.py
```

This opens a window and prints the seed, behavior and agent count, for
example `seed=42 behavior=random_walk agents=5`.

| Key                | Action                       |
|--------------------|------------------------------|
| Arrow up / down    | Move the camera forward/back |
| Arrow left / right | Move the camera left/right   |
| Q                  | Quit                         |

### Headless runs and episode export

```bash
python main.py --headless                        # 600 steps of 0.05 s, seed 42
python main.py --headless --steps 2000 --seed 7 --dt 0.02
python main.py --headless --export-path /tmp/episodes --config my_config.yaml
```

A headless run opens no window and does not create a ShowBase. It
steps the simulation `simulation.steps` times by the fixed
`simulation.dt` and writes the episode to
`<export_path>/episode_<behavior>_seed<seed>.json`. Each flag overrides
the matching key under `simulation:` in the config. `--no-headless`
forces the viewer even when the config says `headless: true`. Run
`python main.py --help` for the full list. Only headless runs record
episodes; the viewer does not.

## Tests

```bash
pytest
```

`tests/conftest.py` sets Panda3D's `window-type none` and
`audio-library-name null` before anything else loads, so the tests never
open a window or an audio device. That includes the viewer smoke test.
`.github/workflows/ci.yml` runs the suite on every push to `main` and on
every pull request.

## Architecture

```
main.py                   command line: load config, apply flags, run headless or open the viewer
config.yaml               every tuneable parameter
simulation/config.py      load_config(): parse the YAML once; fill in a seed if it is null
simulation/core.py        Simulation: build agents from the config, step(dt); no window
simulation/collision.py   CollisionSystem: CollisionTraverser + CollisionSphere per agent +
                          CollisionHandlerQueue; separates and bounces touching agents
simulation/headless.py    run_headless(): fixed-dt run of N steps, recorded frame by frame
simulation/logger.py      EpisodeLogger: per-step agent records, written as one JSON file
simulation/world.py       SimulationWorld (ShowBase): ground, lights, camera, FPS overlay;
                          steps the Simulation once per rendered frame
agents/agent.py           Agent: position, velocity, heading; moves at up to agents.speed
                          and is clamped so its sphere stays inside the world
agents/visuals.py         attach_lod_model(): the two-level LOD sphere (viewer only)
behaviors/base.py         Behavior: abstract base class, decide(agent, dt) -> direction,
                          optional on_collision(agent, normal)
behaviors/random_walk.py  RandomWalk: random heading, a new one every change_interval seconds
behaviors/seek_target.py  SeekTarget: head for a random target, pick a new one on arrival
behaviors/registry.py     maps the names used in config.yaml to behavior classes
tests/                    pytest suite (headless)
```

On each step every agent calls its behavior's `decide(agent, dt)`. The
result is a direction on the ground plane, and its length is the
fraction of top speed to use (anything longer than 1 is capped at 1).
The agent then moves and is clamped to the world.

**Collisions.** After all agents have moved, `CollisionSystem` runs a
`CollisionTraverser` over the simulation's scene graph. Every agent has
a `CollisionSphere` of its radius that is both a "from" and an "into"
object, so each touching pair produces two queue entries; they are
reduced to one `(a, b)` pair with `a < b`. Pairs are resolved in id
order:

1. Each agent is pushed back by half the overlap along the line between
   their centres, so they just touch (unless the world edge stops one).
2. An agent moving towards the other has its velocity mirrored off that
   line.
3. Both agents' behaviors get an `on_collision` call. `random_walk`
   mirrors its walking direction the same way. `seek_target` picks a new
   target.

Only agents collide with agents; the world edge is handled by clamping.
Each collider is tested against every agent sphere on every step (there
is no spatial partitioning), and pushing one pair apart can make another
pair touch, which is resolved on the next step. Agents can spawn
overlapping; the first step pushes them apart.

**Reproducibility.** `Simulation` seeds a master `random.Random` with
`simulation.seed` and gives each agent its own stream from it. Each
agent's stream picks its spawn point and is passed to its behavior.
The same seed and the same sequence of `dt` values give identical
trajectories. The viewer steps by real frame time, so two windowed runs
only match if their frame times match.

**Adding a behavior.** Subclass `Behavior`, set `name`, implement
`decide(agent, dt)`, and add the class to `BEHAVIORS` in
`behaviors/registry.py`. If it has parameters, override `from_config` to
read them from `cfg["behaviors"][name]`. To react to collisions,
override `on_collision(agent, normal)`.

## Episode files

```json
{
  "schema_version": 2,
  "metadata": {
    "seed": 42, "behavior": "random_walk", "agent_count": 5,
    "dt": 0.05, "steps": 600, "collision_count": 2,
    "config": {"...": "the full config of the run, command-line overrides included"}
  },
  "frames": [
    {"step": 0, "time": 0.0, "agents": ["...spawn state of every agent..."],
     "collisions": []},
    {"step": 1, "time": 0.05, "agents": [
      {"id": 0, "behavior": "random_walk",
       "position": [-14.794538, -15.161121, 1.0],
       "velocity": [4.257946, 6.772732], "heading": 57.842854},
      "...one record per agent..."
    ], "collisions": [[0, 3]]},
    "...one frame per step..."
  ]
}
```

(Values from the default config, seed 42.)

- Frame `k` is the state after `k` steps. Frame 0 is the spawn state, so a run of N steps has N + 1 frames.
- `collisions` lists the `[a, b]` id pairs (`a < b`) that touched during that step and were then pushed apart. `metadata.collision_count` is the total over the run. In the example, agents 0 and 3 spawned overlapping and were separated on step 1.
- `position` is in world units; `z` is always the sphere radius, so agents stay on the ground. `velocity` is in units per second on the ground plane. `heading` is in degrees, counter-clockwise from +X, in `[0, 360)`. Values are rounded to 6 decimal places.
- Re-running with the same config and flags on the same platform rewrites the file byte for byte (`tests/test_episode.py`).
- With the defaults (5 agents, 600 steps) a file is about 400 KB.
- Schema version 1 (before collisions) had no `collisions` or `collision_count` fields.

## Configuration reference

| Key | Default | Meaning |
|-----|---------|---------|
| `world.size` | `100` | Side length of the square ground plane, in world units |
| `world.ground_color` | `[0.3, 0.6, 0.3, 1.0]` | Ground RGBA |
| `agents.count` | `5` | Number of agents |
| `agents.speed` | `8.0` | Top speed, units per second |
| `agents.size` | `1.0` | Sphere radius |
| `agents.color` | `[0.8, 0.2, 0.2, 1.0]` | RGBA of the near LOD level; the far level is drawn bluer |
| `agents.spawn_range` | `20.0` | Agents spawn uniformly in `[-spawn_range, spawn_range]` on x and y, capped at the world edge |
| `agents.behavior` | `random_walk` | `random_walk` or `seek_target` |
| `behaviors.random_walk.change_interval` | `1.0` | Seconds of simulated time between direction changes |
| `behaviors.seek_target.arrive_radius` | `1.0` | Distance at which a target counts as reached |
| `collisions.enabled` | `true` | Detect touching agents, push them apart and bounce them |
| `lod.near` | `30.0` | The near sphere is drawn up to this camera distance |
| `lod.far` | `80.0` | The far sphere is drawn from `lod.near` to this distance; beyond it the agent is not drawn |
| `simulation.seed` | `42` | Seed for all randomness; `null` draws a fresh seed, which is printed. Flag: `--seed` |
| `simulation.headless` | `false` | `true` runs without a window and exports the episode. Flag: `--headless` / `--no-headless` |
| `simulation.steps` | `600` | Headless: number of fixed steps. Flag: `--steps` |
| `simulation.dt` | `0.05` | Headless: fixed time step in seconds. Flag: `--dt` |
| `simulation.export_path` | `"episodes/"` | Headless: directory the episode JSON is written to (created if missing; `episodes/` is gitignored). Flag: `--export-path` |
| `simulation.fps_overlay` | `true` | Show the FPS and agent count on screen |

## Status

Working:

- Windowed viewer with a ground plane, lighting, arrow-key camera and an FPS overlay
- Two behaviors, `random_walk` and `seek_target`, behind a common `Behavior` interface, chosen in `config.yaml`
- Seeded, reproducible simulation core that runs without a window
- Headless mode with a fixed time step and JSON episode export, configured in `config.yaml` or with command-line flags
- Agent-agent collision detection with Panda3D's `CollisionTraverser`, a separate-and-bounce response, and per-step collision pairs in the episode log
- Two-level LOD per agent
- Headless pytest suite, run in GitHub Actions CI

Planned, not implemented yet:

- A cheaper far LOD level. Today both levels load the same sphere model and the far one is only drawn smaller, so it saves no rendering work.

Developed with AI pair-programming assistance (Claude Code).

## License

MIT. See [LICENSE](LICENSE).
