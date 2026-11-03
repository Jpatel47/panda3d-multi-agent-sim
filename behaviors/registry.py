"""Maps the behavior names used in config.yaml to behavior classes."""
from behaviors.random_walk import RandomWalk
from behaviors.seek_target import SeekTarget

BEHAVIORS = {cls.name: cls for cls in (RandomWalk, SeekTarget)}


def create_behavior(name, rng, cfg):
    """Instantiate the behavior registered as `name`, configured from `cfg`."""
    try:
        cls = BEHAVIORS[name]
    except KeyError:
        known = ", ".join(sorted(BEHAVIORS))
        raise ValueError(
            f"Unknown behavior {name!r} in config; expected one of: {known}"
        ) from None
    return cls.from_config(rng, cfg)
