import argparse

from simulation.config import load_config
from simulation.core import Simulation
from simulation.headless import episode_path, run_headless


def _positive(convert):
    def parse(text):
        value = convert(text)
        if value <= 0:
            raise argparse.ArgumentTypeError(f"must be positive, got {text}")
        return value
    # argparse names the type in its error messages ("invalid int value").
    parse.__name__ = convert.__name__
    return parse


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Run the Panda3D multi-agent simulation. Options that "
                    "are not given keep their value from the config file.")
    parser.add_argument("--config", default="config.yaml",
                        help="path to the YAML config (default: %(default)s)")
    parser.add_argument("--headless", action=argparse.BooleanOptionalAction,
                        help="run without a window for a fixed number of "
                             "steps and export the episode as JSON "
                             "(simulation.headless)")
    parser.add_argument("--steps", type=_positive(int),
                        help="headless: number of steps (simulation.steps)")
    parser.add_argument("--dt", type=_positive(float),
                        help="headless: fixed time step in seconds "
                             "(simulation.dt)")
    parser.add_argument("--seed", type=int,
                        help="seed for all randomness (simulation.seed)")
    parser.add_argument("--export-path",
                        help="headless: directory for the episode file "
                             "(simulation.export_path)")
    return parser.parse_args(argv)


def apply_overrides(cfg, args):
    """Copy the command-line options that were given into cfg["simulation"]."""
    overrides = {
        "headless": args.headless,
        "steps": args.steps,
        "dt": args.dt,
        "seed": args.seed,
        "export_path": args.export_path,
    }
    for key, value in overrides.items():
        if value is not None:
            cfg["simulation"][key] = value
    return cfg


def main(argv=None):
    args = parse_args(argv)
    # Read the config once and pass the same dict to everything.
    cfg = apply_overrides(load_config(args.config), args)
    sim_cfg = cfg["simulation"]
    summary = (f"seed={sim_cfg['seed']} behavior={cfg['agents']['behavior']} "
               f"agents={cfg['agents']['count']}")

    if sim_cfg["headless"]:
        episode = run_headless(cfg)
        path = episode.write(episode_path(cfg))
        print(f"{summary} steps={sim_cfg['steps']} dt={sim_cfg['dt']} "
              f"-> {path}")
        return path

    # Imported here so that headless runs never load ShowBase.
    from simulation.world import SimulationWorld

    print(summary)
    world = SimulationWorld(cfg, Simulation(cfg))
    world.run()


if __name__ == "__main__":
    main()
