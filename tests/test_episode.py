"""Headless runs and the JSON episode export."""
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

import main
from simulation.core import Simulation
from simulation.headless import run_headless
from simulation.logger import SCHEMA_VERSION, agent_state

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "config.yaml"


def _export(out_dir, *args):
    """Run main.py headless into out_dir; return the file path and its JSON."""
    path = main.main(["--config", str(CONFIG_PATH), "--headless",
                      "--export-path", str(out_dir), *args])
    with open(path) as f:
        return path, json.load(f)


def test_same_seed_writes_byte_identical_files(tmp_path):
    path, _ = _export(tmp_path, "--steps", "120", "--seed", "7")
    first = Path(path).read_bytes()
    Path(path).unlink()

    # Same options, including the export path, which the config snapshot
    # records: the rewritten file must match byte for byte.
    again, _ = _export(tmp_path, "--steps", "120", "--seed", "7")
    assert again == path
    assert Path(again).read_bytes() == first


def test_different_seed_writes_a_different_episode(tmp_path):
    _, a = _export(tmp_path / "a", "--steps", "50", "--seed", "1")
    _, b = _export(tmp_path / "b", "--steps", "50", "--seed", "2")
    assert a["frames"] != b["frames"]


def test_schema(cfg, tmp_path):
    path, episode = _export(tmp_path, "--steps", "40", "--dt", "0.1",
                            "--seed", "3")
    count = cfg["agents"]["count"]

    assert path.endswith("episode_random_walk_seed3.json")
    assert set(episode) == {"schema_version", "metadata", "frames"}
    assert episode["schema_version"] == SCHEMA_VERSION

    meta = episode["metadata"]
    assert meta["seed"] == 3
    assert meta["behavior"] == "random_walk"
    assert meta["agent_count"] == count
    assert meta["dt"] == 0.1
    assert meta["steps"] == 40
    assert meta["collision_count"] == sum(len(f["collisions"])
                                          for f in episode["frames"])
    # The snapshot is the config the run actually used, overrides included.
    assert meta["config"]["simulation"]["seed"] == 3
    assert meta["config"]["simulation"]["steps"] == 40
    assert meta["config"]["agents"] == cfg["agents"]

    frames = episode["frames"]
    assert len(frames) == 41                    # spawn state + one per step
    for k, frame in enumerate(frames):
        assert set(frame) == {"step", "time", "agents", "collisions"}
        assert all(len(pair) == 2 and pair[0] < pair[1]
                   for pair in frame["collisions"])
        assert frame["step"] == k
        assert frame["time"] == pytest.approx(k * 0.1)
        assert [a["id"] for a in frame["agents"]] == list(range(count))
        for agent in frame["agents"]:
            assert set(agent) == {"id", "behavior", "position", "velocity",
                                  "heading"}
            assert agent["behavior"] == "random_walk"
            assert len(agent["position"]) == 3
            assert len(agent["velocity"]) == 2
            assert 0.0 <= agent["heading"] < 360.0


def test_frames_match_stepping_the_simulation_directly(cfg):
    cfg["agents"]["behavior"] = "seek_target"
    cfg["simulation"].update(steps=25, dt=0.2)
    episode = run_headless(cfg)

    sim = Simulation(cfg)
    for _ in range(25):
        sim.step(0.2)
    assert episode.frames[-1]["agents"] == [agent_state(a) for a in sim.agents]


def test_heading_and_velocity_agree(tmp_path):
    _, episode = _export(tmp_path, "--steps", "30")
    for frame in episode["frames"][1:]:
        for agent in frame["agents"]:
            vx, vy = agent["velocity"]
            expected = math.degrees(math.atan2(vy, vx))
            # Compare as angles, so 359.9999 and 0.0 count as equal.
            difference = (agent["heading"] - expected + 180.0) % 360.0 - 180.0
            assert abs(difference) < 1e-3


def test_headless_and_export_path_can_come_from_the_config(cfg, tmp_path):
    cfg["simulation"].update(headless=True, steps=5,
                             export_path=str(tmp_path / "nested" / "dir"))
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(cfg))

    path = main.main(["--config", str(config_path)])
    assert path.startswith(str(tmp_path / "nested" / "dir"))
    with open(path) as f:
        assert json.load(f)["metadata"]["steps"] == 5


@pytest.mark.parametrize("flag,value", [("--steps", "0"), ("--steps", "-3"),
                                        ("--dt", "0"), ("--steps", "1.5")])
def test_rejects_bad_step_options(flag, value, capsys):
    with pytest.raises(SystemExit):
        main.parse_args([flag, value])
    assert f"argument {flag}:" in capsys.readouterr().err


def test_run_headless_rejects_bad_config_values(cfg):
    cfg["simulation"]["steps"] = 0
    with pytest.raises(ValueError, match="simulation.steps"):
        run_headless(cfg)
    cfg["simulation"].update(steps=10, dt=0)
    with pytest.raises(ValueError, match="simulation.dt"):
        run_headless(cfg)


def test_command_line_entry_point(tmp_path):
    result = subprocess.run(
        [sys.executable, "main.py", "--headless", "--steps", "10",
         "--seed", "5", "--export-path", str(tmp_path)],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stderr
    out = tmp_path / "episode_random_walk_seed5.json"
    assert f"-> {out}" in result.stdout
    assert json.loads(out.read_text())["metadata"]["steps"] == 10
