"""Supervisor agent for routing health queries and handling UI utilities."""

from __future__ import annotations

import logging
from typing import Final

from agents import Agent, RunContextWrapper, function_tool, handoff
from chatkit.agents import AgentContext, ClientToolCall

from .model import MODEL

# NOTE: Must match frontend tool name
CLIENT_THEME_TOOL_NAME: Final[str] = "switch_theme"
SUPPORTED_COLOR_SCHEMES: Final[frozenset[str]] = frozenset({"light", "dark"})


SUPERVISOR_INSTRUCTIONS = """You are a supervisor that routes user queries to appropriate specialists.
Never answer health questions yourself, only focus on triage.
You can also handle basic UI requests using your tools."""


def _normalize_color_scheme(value: str) -> str:
    """Normalize color scheme input to 'light' or 'dark'."""
    normalized = str(value).strip().lower()
    if normalized in SUPPORTED_COLOR_SCHEMES:
        return normalized
    if "dark" in normalized:
        return "dark"
    if "light" in normalized:
        return "light"
    raise ValueError("Theme must be either 'light' or 'dark'.")


@function_tool(
    description_override="Switch the chat interface between light and dark color schemes. Use this when the user requests to change the theme, switch to dark mode, light mode, or change the appearance. Accepts 'light' or 'dark' as the theme parameter."
)
async def switch_theme(
    ctx: RunContextWrapper[AgentContext],
    theme: str,
) -> dict[str, str] | None:
    """Switch the chat interface theme between light and dark modes."""
    logging.debug(f"Switching theme to {theme}")
    try:
        requested = _normalize_color_scheme(theme)
        ctx.context.client_tool_call = ClientToolCall(
            name=CLIENT_THEME_TOOL_NAME,
            arguments={"theme": requested},
        )
        return {"theme": requested}
    except Exception:
        logging.exception("Failed to switch theme")
        return None


def create_supervisor_agent(agents: list[Agent[AgentContext]]) -> Agent[AgentContext]:
    """Create a generic supervisor agent that routes queries to provided agents."""
    return Agent(
        name="Supervisor",
        model=MODEL,
        instructions=SUPERVISOR_INSTRUCTIONS,
        tools=[switch_theme],
        handoffs=[handoff(agent) for agent in agents],
    )
