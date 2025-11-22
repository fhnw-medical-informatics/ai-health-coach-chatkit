"""Central application configuration: models and agent names."""

from __future__ import annotations

# Model selection used by all agents

MODEL = "gpt-4.1-mini"

# Agent names
SUPERVISOR_AGENT_NAME = "Supervisor"
PHARMACIST_AGENT_NAME = "Pharmacist"
PSYCHOLOGIST_AGENT_NAME = "Psychologist"


def agent_name_prefix_instruction(agent_name: str) -> str:
    """Generate the generic instruction for agents to prefix their responses with their name in bold."""
    return f'IMPORTANT: Always start your response with **{agent_name}**: <your response> as the very first thing you output (asterisks as markdown bold are important).'


