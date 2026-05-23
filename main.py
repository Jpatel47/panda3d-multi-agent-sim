import yaml
from simulation.world import SimulationWorld
from agents.agent import Agent
from behaviors.random_walk import RandomWalk


def main():
    with open("config.yaml", "r") as f:
        cfg = yaml.safe_load(f)

    world = SimulationWorld("config.yaml")

    for i in range(cfg["agents"]["count"]):
        agent = Agent(world, i, cfg["agents"])
        agent.set_behavior(RandomWalk())
        world.register_agent(agent)

    def update_agents(task):
        dt = globalClock.getDt()
        for agent in world.agents:
            agent.update(dt)
        return task.cont

    world.taskMgr.add(update_agents, "update_agents")
    world.run()


if __name__ == "__main__":
    main()
