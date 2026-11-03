"""Visible models for agents. Only the windowed viewer uses this."""
from panda3d.core import LODNode

SPHERE_MODEL = "models/misc/sphere"


def attach_lod_model(agent, loader, agents_cfg, lod_cfg):
    """
    Attach a two-level LOD sphere under agent.node and return its NodePath.

    The near level is shown up to lod.near units from the camera, the far
    level from lod.near to lod.far, and nothing beyond that. Both levels use
    Panda3D's bundled sphere model; the far one is drawn at half scale with
    a bluer tint, so it is not cheaper to render yet.
    """
    size = agents_cfg["size"]
    color = agents_cfg["color"]

    lod = LODNode(f"agent_{agent.agent_id}_lod")
    lod_np = agent.node.attachNewNode(lod)

    high = loader.loadModel(SPHERE_MODEL)
    high.setScale(size)
    high.setColor(color[0], color[1], color[2], color[3])
    high.reparentTo(lod_np)
    lod.addSwitch(lod_cfg["near"], 0)

    low = loader.loadModel(SPHERE_MODEL)
    low.setScale(size * 0.5)
    low.setColor(color[0], color[1], color[2] + 0.3, color[3])
    low.reparentTo(lod_np)
    lod.addSwitch(lod_cfg["far"], lod_cfg["near"])

    return lod_np
