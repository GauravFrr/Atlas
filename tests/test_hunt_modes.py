"""Production hunt mode selection."""

from config import Settings
from core.lead_sources import PRODUCTION_HUNT_MODES, available_hunt_modes


def test_empty_uses_production_modes() -> None:
    s = Settings(agent_env="production", autopilot_hunt_modes="")
    assert available_hunt_modes(s) == PRODUCTION_HUNT_MODES


def test_m10_only_expands_in_production() -> None:
    s = Settings(agent_env="production", autopilot_hunt_modes="m10_no_website")
    assert available_hunt_modes(s) == PRODUCTION_HUNT_MODES


def test_m10_alias_expands_in_production() -> None:
    s = Settings(agent_env="production", autopilot_hunt_modes="no_website")
    assert available_hunt_modes(s) == PRODUCTION_HUNT_MODES


def test_multi_mode_explicit_respected() -> None:
    s = Settings(agent_env="production", autopilot_hunt_modes="m02_outdated,m24_chatbot")
    assert available_hunt_modes(s) == ["m02_outdated", "m24_chatbot"]
