"""Psychologist agent for mental health support."""

from __future__ import annotations

from agents import Agent
from chatkit.agents import AgentContext

from .config import MODEL, PSYCHOLOGIST_AGENT_NAME, agent_name_prefix_instruction

PSYCHOLOGIST_INSTRUCTIONS = f"""You are a psychologist who specializes in supporting patients with mental health struggles.
Please be empathetic and supportive.
For serious mental health crises, encourage immediate professional help.

{agent_name_prefix_instruction(PSYCHOLOGIST_AGENT_NAME)}"""


def create_psychologist_agent() -> Agent[AgentContext]:
    """Create the psychologist agent specialized in mental health support."""
    return Agent(
        name=PSYCHOLOGIST_AGENT_NAME,
        model=MODEL,
        instructions=PSYCHOLOGIST_INSTRUCTIONS,
        tools=[],  # No tools currently
    )
