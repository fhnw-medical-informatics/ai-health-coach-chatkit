"""Psychologist agent for mental health support."""

from __future__ import annotations

from typing import Final

from agents import Agent
from chatkit.agents import AgentContext

from .model import MODEL

PSYCHOLOGIST_AGENT_NAME: Final[str] = "Psychologist"


PSYCHOLOGIST_INSTRUCTIONS = """You are a psychologist who specializes in supporting patients with mental health struggles.
Please be empathetic and supportive.
For serious mental health crises, encourage immediate professional help."""


def create_psychologist_agent() -> Agent[AgentContext]:
    """Create the psychologist agent specialized in mental health support."""
    return Agent(
        name=PSYCHOLOGIST_AGENT_NAME,
        model=MODEL,
        instructions=PSYCHOLOGIST_INSTRUCTIONS,
        tools=[],  # No tools currently
    )
