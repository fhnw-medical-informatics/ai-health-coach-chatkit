"""ChatKit server integration for the boilerplate backend."""

from __future__ import annotations

import inspect
import logging
from datetime import datetime
from typing import Annotated, Any, AsyncIterator, Final, Literal
from uuid import uuid4

from agents import Agent, RunContextWrapper, Runner, function_tool
from chatkit.agents import (
    AgentContext,
    ClientToolCall,
    ThreadItemConverter,
    stream_agent_response,
)
from chatkit.server import ChatKitServer, ThreadItemDoneEvent
from chatkit.types import (
    Attachment,
    ClientToolCallItem,
    HiddenContextItem,
    ThreadItem,
    ThreadMetadata,
    ThreadStreamEvent,
    UserMessageItem,
)
from openai.types.responses import ResponseInputContentParam
from pydantic import ConfigDict, Field

from .constants import INSTRUCTIONS, MODEL
from .medications import Medication, medication_store
from .memory_store import MemoryStore

# If you want to check what's going on under the hood, set this to DEBUG
logging.basicConfig(level=logging.INFO)

SUPPORTED_COLOR_SCHEMES: Final[frozenset[str]] = frozenset({"light", "dark"})
CLIENT_THEME_TOOL_NAME: Final[str] = "switch_theme"


def _normalize_color_scheme(value: str) -> str:
    normalized = str(value).strip().lower()
    if normalized in SUPPORTED_COLOR_SCHEMES:
        return normalized
    if "dark" in normalized:
        return "dark"
    if "light" in normalized:
        return "light"
    raise ValueError("Theme must be either 'light' or 'dark'.")


def _gen_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}"


def _is_tool_completion_item(item: Any) -> bool:
    return isinstance(item, ClientToolCallItem)


class HealthCoachAgentContext(AgentContext):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    store: Annotated[MemoryStore, Field(exclude=True)]
    request_context: dict[str, Any]


async def _stream_saved_hidden(ctx: RunContextWrapper[HealthCoachAgentContext], medication: Medication) -> None:
    await ctx.context.stream(
        ThreadItemDoneEvent(
            item=HiddenContextItem(
                id=_gen_id("msg"),
                thread_id=ctx.context.thread.id,
                created_at=datetime.now(),
                content=(
                    f'<MEDICATION_SAVED id="{medication.id}" threadId="{ctx.context.thread.id}">{medication.name}</MEDICATION_SAVED>'
                ),
            ),
        )
    )


@function_tool(description_override="Record a medication when the user mentions taking, buying, or using any medication. Use your medical knowledge to format the medication name properly (e.g., 'ibuprofen' → 'Ibuprofen', 'vitamin d' → 'Vitamin D', 'omega 3' → 'Omega-3'). The system automatically prevents duplicate medications, so you can safely call this tool each time a medication is mentioned.")
async def save_medication(
    ctx: RunContextWrapper[HealthCoachAgentContext],
    medication_name: str,
) -> dict[str, str] | None:
    try:
        saved = await medication_store.create(name=medication_name)
        await _stream_saved_hidden(ctx, saved)
        print(f"MEDICATION SAVED: {saved}")
        return {"medication_name": saved.name, "status": "saved"}
    except Exception:
        logging.exception("Failed to save medication")
        return None


@function_tool(
    description_override="Switch the chat interface between light and dark color schemes. Use this when the user requests to change the theme, switch to dark mode, light mode, or change the appearance. Accepts 'light' or 'dark' as the theme parameter."
)
async def switch_theme(
    ctx: RunContextWrapper[HealthCoachAgentContext],
    theme: str,
) -> dict[str, str] | None:
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






def _user_message_text(item: UserMessageItem) -> str:
    parts: list[str] = []
    for part in item.content:
        text = getattr(part, "text", None)
        if text:
            parts.append(text)
    return " ".join(parts).strip()


class HealthCoachServer(ChatKitServer[dict[str, Any]]):
    """Health Coach server with medication management and other health features."""

    def __init__(self) -> None:
        self.store: MemoryStore = MemoryStore()
        super().__init__(self.store)
        tools = [save_medication, switch_theme]
        self.assistant = Agent[HealthCoachAgentContext](
            model=MODEL,
            name="Health Coach",
            instructions=INSTRUCTIONS,
            tools=tools,  # type: ignore[arg-type]
        )
        self._thread_item_converter = self._init_thread_item_converter()

    async def respond(
        self,
        thread: ThreadMetadata,
        item: UserMessageItem | None,
        context: dict[str, Any],
    ) -> AsyncIterator[ThreadStreamEvent]:
        agent_context = HealthCoachAgentContext(
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

        # Inject saved medications into the prompt context
        try:
            saved_medications = await medication_store.list_all()
            if saved_medications:
                medications_text = "; ".join([medication.name for medication in saved_medications])
                medications_context = f"You know the following medications about this user: {medications_text}"
                
                if isinstance(agent_input, str):
                    agent_input = f"{medications_context}\n\nCurrent request: {agent_input}"
                elif isinstance(agent_input, dict) and "content" in agent_input:
                    agent_input["content"] = f"{medications_context}\n\nCurrent request: {agent_input['content']}"
        except Exception as e:
            logging.warning(f"Failed to retrieve user medications for context: {e}")

        result = Runner.run_streamed(
            self.assistant,
            agent_input,
            context=agent_context,
        )

        async for event in stream_agent_response(agent_context, result):
            yield event
        return

    async def to_message_content(self, _input: Attachment) -> ResponseInputContentParam:
        raise RuntimeError("File attachments are not supported in this demo.")

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

    async def _add_hidden_item(
        self,
        thread: ThreadMetadata,
        context: dict[str, Any],
        content: str,
    ) -> None:
        await self.store.add_thread_item(
            thread.id,
            HiddenContextItem(
                id=_gen_id("msg"),
                thread_id=thread.id,
                created_at=datetime.now(),
                content=content,
            ),
            context,
        )


def create_chatkit_server() -> HealthCoachServer | None:
    """Return a configured ChatKit server instance if dependencies are available."""
    return HealthCoachServer()
