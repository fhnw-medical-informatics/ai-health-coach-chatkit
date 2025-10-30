"""Use ChatKit widgets to stream agent responses into colored boxes."""

from __future__ import annotations

from typing import Any, AsyncIterator

from chatkit.widgets import Card, Markdown

from .config import agent_background


def _extract_agent_name(ev: Any) -> str | None:
    if hasattr(ev, "new_agent") and getattr(ev.new_agent, "name", None):
        return ev.new_agent.name

    run_item = getattr(ev, "run_item", None)
    if run_item and getattr(run_item, "agent", None):
        agent_obj_or_name = run_item.agent
        return getattr(agent_obj_or_name, "name", None) or str(agent_obj_or_name)

    return None


def _extract_text_delta(ev: Any) -> str:
    data = getattr(ev, "data", None)
    if data is None:
        return ""

    data_type = getattr(data, "type", "")
    if data_type not in (
        "response.output_text.delta",
        "output_text.delta",
        "output_text_delta",
    ):
        return ""

    return getattr(data, "delta", "") or getattr(data, "text", "") or ""


def _make_card(agent_name: str, text: str) -> Card:
    title_md = Markdown(id="agent-title", value=f"**{agent_name}**")
    md = Markdown(id="agent-response", value=text, streaming=True)
    return Card(
        size="md",
        background=agent_background(agent_name),
        children=[title_md, md],
    )


async def generate_agent_response_widget(
    result_stream: Any
) -> AsyncIterator[Card]:
    """Yield streaming `Card` widgets reflecting agent handoffs and text deltas.

    Parameters
    ----------
    result_stream: The streaming result from the Agents SDK (supports `.stream_events()`).
    default_agent_name: Fallback agent name to use before first handoff event.
    """
    current_agent_name = ""
    text_acc = ""

    # Initial empty card so the widget renders immediately
    yield _make_card(current_agent_name, text_acc)

    async for ev in result_stream.stream_events():
        new_name = _extract_agent_name(ev)
        if new_name:
            current_agent_name = new_name
            yield _make_card(current_agent_name, text_acc)
            continue

        delta = _extract_text_delta(ev)
        if not delta:
            continue

        text_acc += delta
        yield _make_card(current_agent_name, text_acc)


