from simulation.config import load_config
from simulation.core import Simulation
from simulation.world import SimulationWorld


def main(config_path="config.yaml"):
    # Read the config once and pass the same dict to everything.
    cfg = load_config(config_path)
    sim = Simulation(cfg)
    print(f"seed={sim.seed} behavior={sim.behavior_name} "
          f"agents={len(sim.agents)}")

    world = SimulationWorld(cfg, sim)
    world.run()


if __name__ == "__main__":
    main()
