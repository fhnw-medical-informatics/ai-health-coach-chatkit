"""ChatKit server integration for the health coach backend."""

from __future__ import annotations

import asyncio
import inspect
import logging
from typing import Any, AsyncIterator

from agents import Runner
from chatkit.agents import (
    AgentContext,
    ThreadItemConverter,
)
from chatkit.server import stream_widget
from chatkit.server import ChatKitServer
from chatkit.types import (
    Attachment,
    ClientToolCallItem,
    ThreadItem,
    ThreadMetadata,
    ThreadStreamEvent,
    UserMessageItem,
)
from chatkit.widgets import Card, Markdown
from openai.types.responses import ResponseInputContentParam

from .pharmacist import PHARMACIST_AGENT_NAME, create_pharmacist_agent
from .psychologist import PSYCHOLOGIST_AGENT_NAME, create_psychologist_agent
from .supervisor import SUPERVISOR_AGENT_NAME, create_supervisor_agent
from .memory_store import MemoryStore

logging.basicConfig(level=logging.INFO)


AGENT_BACKGROUNDS: dict[str, dict[str, str]] = {
    PSYCHOLOGIST_AGENT_NAME: {"light": "#e6f0ff", "dark": "#1e3a8a"},
    PHARMACIST_AGENT_NAME: {"light": "#e8f8f0", "dark": "#166534"},
    SUPERVISOR_AGENT_NAME: {"light": "#f3f4f6", "dark": "#374151"},
}


class HealthCoachServer(ChatKitServer[dict[str, Any]]):
    """Health Coach server with multi-agent setup for specialized health support."""

    def __init__(self) -> None:
        self.store: MemoryStore = MemoryStore()
        super().__init__(self.store)

        # Create multi-agent setup
        pharmacist = create_pharmacist_agent()
        psychologist = create_psychologist_agent()
        self.assistant = create_supervisor_agent([pharmacist, psychologist])
        self._thread_item_converter = self._init_thread_item_converter()

    async def respond(
        self,
        thread: ThreadMetadata,
        item: UserMessageItem | None,
        context: dict[str, Any],
    ) -> AsyncIterator[ThreadStreamEvent]:
        agent_context = AgentContext(
            thread=thread,
            store=self.store,
            request_context=context,
        )

        target_item: ThreadItem | None = item
        if target_item is None:
            target_item = await self._latest_thread_item(thread, context)

        if target_item is None or _is_tool_completion_item(target_item):
            return

        agent_input = await self._to_agent_input(thread, target_item)
        if agent_input is None:
            return

        # Run the multi-agent supervisor in streaming mode (Agents SDK stream)
        result = Runner.run_streamed(
            self.assistant,
            agent_input,
            context=agent_context,
        )

        # Output agent response as a widget so we can style it (and update live)
        async def widget_generator():
            def extract_agent_name(ev: Any) -> str | None:
                if hasattr(ev, "new_agent") and getattr(ev.new_agent, "name", None):
                    return ev.new_agent.name

                run_item = getattr(ev, "run_item", None)
                if run_item and getattr(run_item, "agent", None):
                    agent_obj_or_name = run_item.agent
                    return getattr(agent_obj_or_name, "name", None) or str(agent_obj_or_name)

                return None

            def extract_text_delta(ev: Any) -> str:
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

            def make_card(agent_name: str, text: str) -> Card:
                md = Markdown(id="agent-response", value=text, streaming=True)
                return Card(
                    size="md",
                    background=agent_background(agent_name),
                    children=[md],
                )

            # Start with whoever is currently "active" (likely Supervisor)
            current_agent_name = getattr(self.assistant, "name", SUPERVISOR_AGENT_NAME)
            text_acc = ""

            # Yield initial empty card so the shell renders immediately
            yield make_card(current_agent_name, text_acc)

            # Iterate the *Agents SDK* events directly so we can:
            #  - detect handoffs to sub-agents and recolor the card
            #  - append token deltas to the Markdown
            async for ev in result.stream_events():
                new_name = extract_agent_name(ev)
                if new_name:
                    current_agent_name = new_name
                    yield make_card(current_agent_name, text_acc)
                    continue

                delta = extract_text_delta(ev)
                if not delta:
                    continue

                text_acc += delta
                yield make_card(current_agent_name, text_acc)

        # Stream the widget updates to ChatKit UI
        async for ev in stream_widget(
            thread,
            widget_generator(),
            generate_id=lambda item_type: self.store.generate_item_id(item_type, thread, context),
        ):
            yield ev
        return

    async def _latest_thread_item(
        self, thread: ThreadMetadata, context: dict[str, Any]
    ) -> ThreadItem | None:
        try:
            items = await self.store.load_thread_items(thread.id, None, 1, "desc", context)
        except Exception:  # pragma: no cover - defensive
            return None

        return items.data[0] if getattr(items, "data", None) else None

    async def _to_agent_input(
        self,
        thread: ThreadMetadata,
        item: ThreadItem,
    ) -> Any | None:
        if _is_tool_completion_item(item):
            return None

        converter = getattr(self, "_thread_item_converter", None)
        if converter is not None:
            for attr in (
                "to_input_item",
                "convert",
                "convert_item",
                "convert_thread_item",
            ):
                method = getattr(converter, attr, None)
                if method is None:
                    continue
                call_args: list[Any] = [item]
                call_kwargs: dict[str, Any] = {}
                try:
                    signature = inspect.signature(method)
                except (TypeError, ValueError):
                    signature = None

                if signature is not None:
                    params = [
                        parameter
                        for parameter in signature.parameters.values()
                        if parameter.kind
                        not in (
                            inspect.Parameter.VAR_POSITIONAL,
                            inspect.Parameter.VAR_KEYWORD,
                        )
                    ]
                    if len(params) >= 2:
                        next_param = params[1]
                        if next_param.kind in (
                            inspect.Parameter.POSITIONAL_ONLY,
                            inspect.Parameter.POSITIONAL_OR_KEYWORD,
                        ):
                            call_args.append(thread)
                        else:
                            call_kwargs[next_param.name] = thread

                result = method(*call_args, **call_kwargs)
                if inspect.isawaitable(result):
                    return await result
                return result

        if isinstance(item, UserMessageItem):
            return _user_message_text(item)

        return None

    def _init_thread_item_converter(self) -> Any | None:
        converter_cls = ThreadItemConverter
        if converter_cls is None or not callable(converter_cls):
            return None

        attempts: tuple[dict[str, Any], ...] = (
            {"to_message_content": self.to_message_content},
            {"message_content_converter": self.to_message_content},
            {},
        )

        for kwargs in attempts:
            try:
                return converter_cls(**kwargs)
            except TypeError:
                continue
        return None

    async def to_message_content(self, _input: Attachment) -> ResponseInputContentParam:
        raise RuntimeError("File attachments are not supported in this demo.")


def create_chatkit_server() -> HealthCoachServer | None:
    return HealthCoachServer()

def agent_background(agent_name: str) -> dict[str, str]:
    return AGENT_BACKGROUNDS.get(agent_name, {"light": "#f3f4f6", "dark": "#374151"})


def _is_tool_completion_item(item: Any) -> bool:
    return isinstance(item, ClientToolCallItem)


def _user_message_text(item: UserMessageItem) -> str:
    parts: list[str] = []
    for part in item.content:
        text = getattr(part, "text", None)
        if text:
            parts.append(text)
    return " ".join(parts).strip()
