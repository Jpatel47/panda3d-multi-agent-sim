"""Behavior interface and the config-driven behavior registry."""
import random

import pytest

from behaviors.base import Behavior
from behaviors.registry import BEHAVIORS, create_behavior
from behaviors.random_walk import RandomWalk
from behaviors.seek_target import SeekTarget


def test_registry_lists_every_behavior_by_its_config_name():
    assert BEHAVIORS == {"random_walk": RandomWalk, "seek_target": SeekTarget}


@pytest.mark.parametrize("name", sorted(BEHAVIORS))
def test_create_behavior_builds_the_named_behavior(cfg, name):
    behavior = create_behavior(name, random.Random(0), cfg)
    assert isinstance(behavior, Behavior)
    assert type(behavior) is BEHAVIORS[name]
    assert behavior.name == name


def test_parameters_come_from_config(cfg):
    cfg["behaviors"]["random_walk"]["change_interval"] = 2.5
    cfg["behaviors"]["seek_target"]["arrive_radius"] = 3.0
    rng = random.Random(0)
    assert create_behavior("random_walk", rng, cfg).change_interval == 2.5
    assert create_behavior("seek_target", rng, cfg).arrive_radius == 3.0


def test_unknown_name_is_rejected_with_the_known_names(cfg):
    with pytest.raises(ValueError, match="random_walk, seek_target"):
        create_behavior("teleport", random.Random(0), cfg)


def test_behavior_must_implement_decide():
    class NoDecide(Behavior):
        name = "no_decide"

    with pytest.raises(TypeError):
        Behavior(random.Random(0))
    with pytest.raises(TypeError):
        NoDecide(random.Random(0))
