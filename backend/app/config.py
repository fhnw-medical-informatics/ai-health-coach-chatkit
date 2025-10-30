"""Central application configuration: models and agent UI colors."""

from __future__ import annotations

# Model selection used by all agents

MODEL = "gpt-4.1-mini"

# Agent names
SUPERVISOR_AGENT_NAME = "Supervisor"
PHARMACIST_AGENT_NAME = "Pharmacist"
PSYCHOLOGIST_AGENT_NAME = "Psychologist"


# Background colors per agent for light/dark themes
AGENT_BACKGROUNDS: dict[str, dict[str, str]] = {
    PSYCHOLOGIST_AGENT_NAME: {"light": "#e6f0ff", "dark": "#1e3a8a"},
    PHARMACIST_AGENT_NAME: {"light": "#e8f8f0", "dark": "#166534"},
    SUPERVISOR_AGENT_NAME: {"light": "#f3f4f6", "dark": "#374151"},
}


def agent_background(agent_name: str) -> dict[str, str]:
    return AGENT_BACKGROUNDS.get(agent_name) or AGENT_BACKGROUNDS[SUPERVISOR_AGENT_NAME]


