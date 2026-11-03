"""Shared pytest setup: keep Panda3D headless and free of side effects."""
from pathlib import Path

import pytest
from panda3d.core import loadPrcFileData

from simulation.config import load_config

# This runs before any test module is imported, so it takes effect before
# anything creates a ShowBase or loads a model: never open a window, never
# open an audio device, and never write a model cache into the user's home.
loadPrcFileData("tests", "window-type none\n"
                         "audio-library-name null\n"
                         "model-cache-dir \n")

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"


@pytest.fixture
def cfg():
    """A fresh copy of the repository's config.yaml for each test."""
    return load_config(CONFIG_PATH)
