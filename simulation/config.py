"""Load config.yaml once; the resulting dict is passed to every component."""
import random

import yaml


def load_config(path="config.yaml"):
    """Read the YAML config file and return it as a dict.

    A missing or null simulation.seed is replaced with a freshly drawn one,
    so every run still has a concrete seed that can be used to reproduce it.
    """
    with open(path, "r") as f:
        cfg = yaml.safe_load(f)

    if cfg["simulation"].get("seed") is None:
        cfg["simulation"]["seed"] = random.SystemRandom().randrange(2 ** 32)
    return cfg
