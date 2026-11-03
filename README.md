# panda3d-multi-agent-sim

A small multi-agent simulation written in Python on top of
[Panda3D](https://www.panda3d.org/). Agents move around a square ground
plane, each driven by a pluggable behavior that `config.yaml` selects.
Every run can be reproduced from one seed. The simulation core needs no
window, so the whole thing is unit-tested headless. A Panda3D viewer
draws the agents as two-level LOD spheres.

## Setup

Python 3.9 or newer. CI runs the tests on Python 3.9 and 3.11.

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
main.py                   entry point: load config, build Simulation, open the viewer
config.yaml               every tuneable parameter
simulation/config.py      load_config(): parse the YAML once; fill in a seed if it is null
simulation/core.py        Simulation: build agents from the config, step(dt); no window
simulation/world.py       SimulationWorld (ShowBase): ground, lights, camera, FPS overlay;
                          steps the Simulation once per rendered frame
agents/agent.py           Agent: position, velocity, heading; moves at up to agents.speed
                          and is clamped so its sphere stays inside the world
agents/visuals.py         attach_lod_model(): the two-level LOD sphere (viewer only)
behaviors/base.py         Behavior: abstract base class, decide(agent, dt) -> direction
behaviors/random_walk.py  RandomWalk: random heading, a new one every change_interval seconds
behaviors/seek_target.py  SeekTarget: head for a random target, pick a new one on arrival
behaviors/registry.py     maps the names used in config.yaml to behavior classes
tests/                    pytest suite (headless)
```

On each step every agent calls its behavior's `decide(agent, dt)`. The
result is a direction on the ground plane, and its length is the
fraction of top speed to use (anything longer than 1 is capped at 1).
The agent then moves and is clamped to the world.

**Reproducibility.** `Simulation` seeds a master `random.Random` with
`simulation.seed` and gives each agent its own stream from it. Each
agent's stream picks its spawn point and is passed to its behavior.
The same seed and the same sequence of `dt` values give identical
trajectories. The viewer steps by real frame time, so two windowed runs
only match if their frame times match.

**Adding a behavior.** Subclass `Behavior`, set `name`, implement
`decide(agent, dt)`, and add the class to `BEHAVIORS` in
`behaviors/registry.py`. If it has parameters, override `from_config` to
read them from `cfg["behaviors"][name]`.

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
| `lod.near` | `30.0` | The near sphere is drawn up to this camera distance |
| `lod.far` | `80.0` | The far sphere is drawn from `lod.near` to this distance; beyond it the agent is not drawn |
| `simulation.seed` | `42` | Seed for all randomness; `null` draws a fresh seed, which is printed |
| `simulation.fps_overlay` | `true` | Show the FPS and agent count on screen |
| `simulation.headless` | `false` | Not used yet (see Status) |
| `simulation.export_path` | `"episodes/"` | Not used yet (see Status) |

## Status

Working:

- Windowed viewer with a ground plane, lighting, arrow-key camera and an FPS overlay
- Two behaviors, `random_walk` and `seek_target`, behind a common `Behavior` interface, chosen in `config.yaml`
- Seeded, reproducible simulation core that runs without a window
- Two-level LOD per agent
- Headless pytest suite, run in GitHub Actions CI

Planned, not implemented yet:

- Headless mode and JSON episode export (`simulation.headless`, `simulation.export_path`)
- Agent-agent collision detection
- A cheaper far LOD level. Today both levels load the same sphere model and the far one is only drawn smaller, so it saves no rendering work.

Developed with AI pair-programming assistance (Claude Code).

## License

MIT. See [LICENSE](LICENSE).
