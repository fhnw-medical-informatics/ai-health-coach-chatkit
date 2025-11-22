"""ChatKit server integration for the health coach backend."""

from __future__ import annotations

import inspect
from typing import Any, AsyncIterator

from agents import Runner
from chatkit.agents import (
    AgentContext,
    ThreadItemConverter,
    stream_agent_response,
)
from chatkit.server import ChatKitServer
from chatkit.types import (
    Attachment,
    ClientToolCallItem,
    ThreadItem,
    ThreadMetadata,
    ThreadStreamEvent,
    UserMessageItem,
)
from openai.types.responses import ResponseInputContentParam

from .pharmacist import create_pharmacist_agent
from .psychologist import create_psychologist_agent
from .supervisor import create_supervisor_agent
from .memory_store import MemoryStore


def _is_tool_completion_item(item: Any) -> bool:
    return isinstance(item, ClientToolCallItem)


def _user_message_text(item: UserMessageItem) -> str:
    parts: list[str] = []
    for part in item.content:
        text = getattr(part, "text", None)
        if text:
            parts.append(text)
    return " ".join(parts).strip()


def _extract_message_text(item: ThreadItem) -> str | None:
    """Extract text content from any message item type."""
    if isinstance(item, UserMessageItem):
        return _user_message_text(item)
    
    # Try to extract text from other message types (e.g., assistant messages)
    if hasattr(item, "content"):
        content = item.content
        if isinstance(content, list):
            parts: list[str] = []
            for part in content:
                text = getattr(part, "text", None)
                if text:
                    parts.append(text)
            result = " ".join(parts).strip()
            return result if result else None
        elif isinstance(content, str):
            return content.strip() if content.strip() else None
    
    return None


class HealthCoachServer(ChatKitServer[dict[str, Any]]):
    """Health Coach server with multi-agent setup for specialized health support."""

    def __init__(self) -> None:
        self.store = MemoryStore()
        super().__init__(self.store)
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

        # Load full conversation history and convert to agent input
        agent_input = await self._to_agent_input_with_history(thread, target_item, context)
        if agent_input is None:
            return

        result = Runner.run_streamed(
            self.assistant,
            agent_input,
            context=agent_context,
        )

        async for event in stream_agent_response(agent_context, result):
            yield event

    async def to_message_content(self, _input: Attachment) -> ResponseInputContentParam:
        raise RuntimeError("File attachments are not supported")

    def _init_thread_item_converter(self) -> Any | None:
        if not callable(ThreadItemConverter):
            return None

        for kwargs in (
            {"to_message_content": self.to_message_content},
            {"message_content_converter": self.to_message_content},
            {},
        ):
            try:
                return ThreadItemConverter(**kwargs)
            except TypeError:
                continue
        return None

    async def _latest_thread_item(
        self, thread: ThreadMetadata, context: dict[str, Any]
    ) -> ThreadItem | None:
        try:
            items = await self.store.load_thread_items(thread.id, None, 1, "desc", context)
            return items.data[0] if items.data else None
        except Exception:
            return None

    async def _to_agent_input_with_history(
        self,
        thread: ThreadMetadata,
        current_item: ThreadItem,
        context: dict[str, Any],
    ) -> Any | None:
        """Convert thread items to agent input, including full conversation history."""
        if _is_tool_completion_item(current_item):
            return None

        # Load all thread items for full conversation history
        try:
            all_items_page = await self.store.load_thread_items(thread.id, None, 100, "asc", context)
            all_items = all_items_page.data if all_items_page.data else []
        except Exception:
            all_items = []

        # Filter out tool completion items
        conversation_items = [item for item in all_items if not _is_tool_completion_item(item)]

        if not conversation_items:
            return await self._to_agent_input(thread, current_item)

        # Convert all items to agent input format
        messages = []
        
        for item in conversation_items:
            converted = await self._to_agent_input(thread, item)
            if converted is not None:
                # If converter returned a string, convert it to proper message format
                if isinstance(converted, str):
                    # Determine role based on item type
                    role = "user" if isinstance(item, UserMessageItem) else "assistant"
                    messages.append({"role": role, "content": converted})
                else:
                    # Converter returned a proper object, use it as-is
                    messages.append(converted)
            else:
                # Converter didn't work, try extracting text directly
                text = _extract_message_text(item)
                if text:
                    role = "user" if isinstance(item, UserMessageItem) else "assistant"
                    messages.append({"role": role, "content": text})

        if not messages:
            return None

        # Always return the full history as a list
        return messages

    async def _to_agent_input(
        self,
        thread: ThreadMetadata,
        item: ThreadItem,
    ) -> Any | None:
        """Convert a single thread item to agent input format."""
        if _is_tool_completion_item(item):
            return None

        converter = self._thread_item_converter
        if converter:
            for method_name in ("to_input_item", "convert", "convert_item", "convert_thread_item"):
                method = getattr(converter, method_name, None)
                if not method:
                    continue

                call_args = [item]
                call_kwargs = {}

                try:
                    sig = inspect.signature(method)
                    params = [
                        p for p in sig.parameters.values()
                        if p.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
                    ]
                    if len(params) >= 2:
                        if params[1].kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD):
                            call_args.append(thread)
                        else:
                            call_kwargs[params[1].name] = thread
                except (TypeError, ValueError):
                    pass

                result = method(*call_args, **call_kwargs)
                return await result if inspect.isawaitable(result) else result

        if isinstance(item, UserMessageItem):
            return _user_message_text(item)

        return None


def create_chatkit_server() -> HealthCoachServer | None:
    return HealthCoachServer()
