import asyncio
import json
import logging
from typing import Literal

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, MessagesState, START, END

from app.tools import search_flights, find_hotels
from app.safety import TOOL_TIMEOUT_SECS, MSG_TOOL_TIMEOUT, RECURSION_LIMIT
from app.session_store import session_store

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Cancellation sentinel
# ---------------------------------------------------------------------------

class TaskCancelled(Exception):
    """Raised inside a graph node when the session's cancel event is set."""


# ---------------------------------------------------------------------------
# Tools & LLM
# ---------------------------------------------------------------------------

tools = [search_flights, find_hotels]
_tool_map = {t.name: t for t in tools}

llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0)
llm_with_tools = llm.bind_tools(tools)


# ---------------------------------------------------------------------------
# System Prompt — Clarification-First + Language Persistence
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are an expert AI Travel Agent. Your sole purpose is to help users plan trips, \
search for flights, find hotels, and build complete travel itineraries.

CLARIFICATION FIRST — STRICT RULE:
You must NEVER invoke a tool (search_flights or find_hotels) unless ALL required \
parameters have been explicitly confirmed in the conversation. Do not assume, \
infer, or guess any value.

Required parameters before calling search_flights:
  • Origin city or airport code (required — never assume)
  • Destination city or airport code (required — never assume)
  • Departure date in YYYY-MM-DD format (required — never assume)
  • Return date in YYYY-MM-DD format (required for round trips; omit for one-way)
  • Number of passengers (default 1 only if the user has not mentioned travel companions)

Required parameters before calling find_hotels:
  • Destination city (required — never assume)
  • Check-in date in YYYY-MM-DD format (required — never assume)
  • Check-out date in YYYY-MM-DD format (required — never assume)
  • Special requirements e.g. kosher, parking (optional)

If ANY required field is absent or ambiguous, you MUST ask the user to clarify \
before calling a tool. Ask only for the specific missing information — \
do not repeat fields the user already provided.

LANGUAGE PERSISTENCE — STRICT RULE:
Always respond in the same language the user is currently using.
If the user writes in Hebrew (or any non-English language) ALL your responses \
must be in that language — including clarifying questions, error explanations, \
tool-call retry prompts, and result summaries. \
Never switch to English mid-conversation. \
If a tool fails or returns an error, explain it and prompt for correction \
in the user's language.

Guidelines:
- Once you have all required details, call the relevant tool immediately.
- Summarise results concisely: price, duration/stops for flights; stars, nightly \
  rate, and features for hotels.
- If a tool returns a timeout or error, relay it politely and suggest the user try again.

CRITICAL GUARDRAIL:
You must ONLY discuss topics related to travel, flights, hotels, destinations, \
packing tips, visa information, and itinerary planning. \
If the user asks about anything unrelated, politely decline and redirect. \
Example: "I'm specialised in travel planning and can't help with that. \
Is there a trip I can help you plan?"\
"""


# ---------------------------------------------------------------------------
# Pre-Tool Guard — required-parameter specifications
# ---------------------------------------------------------------------------

# Parameters that must be present (non-empty) before a tool may be invoked.
_TOOL_REQUIRED_PARAMS: dict[str, list[str]] = {
    "search_flights": ["origin", "destination", "departure_date"],
    "find_hotels":    ["destination", "check_in", "check_out"],
}

# Human-readable labels used when constructing clarifying questions.
_PARAM_LABELS: dict[str, str] = {
    "origin":         "the departure city or airport",
    "destination":    "the destination city",
    "departure_date": "the departure date (YYYY-MM-DD)",
    "check_in":       "the hotel check-in date (YYYY-MM-DD)",
    "check_out":      "the hotel check-out date (YYYY-MM-DD)",
}


# ---------------------------------------------------------------------------
# State look-back: extraction prompt + helper
# ---------------------------------------------------------------------------

_EXTRACTION_PROMPT_TEMPLATE = """\
Extract travel parameters from the conversation below.
Return ONLY a JSON object with exactly the requested keys. \
Use null for values not found.

Rules:
- Extract ONLY values the user explicitly stated. Never guess or infer.
- Convert natural-language dates to YYYY-MM-DD \
(e.g. "July 15th 2025" → "2025-07-15", "ה-15 ביולי" → "2025-07-15").
- City names: preserve them exactly as stated (e.g. "תל אביב", "Tel Aviv", "Paris").

Keys to extract: {keys}

Key definitions:
  origin         → departure city or airport (e.g. "Tel Aviv", "TLV", "תל אביב")
  destination    → destination city or country (e.g. "Paris", "פריז")
  departure_date → departure date as YYYY-MM-DD
  return_date    → return/arrival date as YYYY-MM-DD
  check_in       → hotel check-in date as YYYY-MM-DD
  check_out      → hotel check-out date as YYYY-MM-DD

Conversation (oldest first):
{history}

Respond with JSON only — no explanation, no markdown fences."""


async def _extract_params_from_history(
    messages: list,
    missing_keys: list[str],
) -> dict[str, str | None]:
    """
    Ask the LLM (no tools) to extract specific travel parameter values
    from the conversation history.

    Returns {param_key: value_or_None} for every requested key.
    Falls back to all-None on any error so the caller can still ask the user.
    """
    history_lines: list[str] = []
    for m in messages:
        if isinstance(m, HumanMessage):
            history_lines.append(f"User: {m.content}")
        elif isinstance(m, AIMessage) and m.content and not m.tool_calls:
            history_lines.append(f"Assistant: {m.content}")

    if not history_lines:
        return {k: None for k in missing_keys}

    prompt_text = _EXTRACTION_PROMPT_TEMPLATE.format(
        keys=", ".join(missing_keys),
        history="\n".join(history_lines),
    )

    try:
        response = await llm.ainvoke([HumanMessage(content=prompt_text)])
        raw = str(response.content).strip()
        # Strip markdown code fences if the model wraps the JSON.
        if raw.startswith("```"):
            raw = raw.split("```")[1].lstrip("json").strip()
        data: dict = json.loads(raw)
        return {k: data.get(k) or None for k in missing_keys}
    except Exception as exc:
        # DEBUG_START
        print(f"[SELF-CORRECTION] extraction LLM call failed: {exc}")
        # DEBUG_END
        return {k: None for k in missing_keys}


# ---------------------------------------------------------------------------
# Cancellation helper
# ---------------------------------------------------------------------------

def _check_cancel(config: RunnableConfig, location: str = "") -> None:
    """
    Raise TaskCancelled if the thread's cancel event has been set.

    Reads thread_id from the LangGraph configurable dict and looks it up in
    the global session_store.  When no event is registered (e.g. the CLI)
    the check is silently skipped.
    """
    thread_id = config.get("configurable", {}).get("thread_id")
    if not thread_id:
        return
    event = session_store.get_cancel_event(thread_id)
    if event and event.is_set():
        # DEBUG_START
        tag = f" [{location}]" if location else ""
        print(f"[CANCEL]{tag} cancellation flag is SET for thread {thread_id[:8]} — raising TaskCancelled")
        # DEBUG_END
        raise TaskCancelled("Request was cancelled by the client.")


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def call_model(state: MessagesState, config: RunnableConfig) -> dict:
    """Invoke the LLM with the system prompt prepended to the current messages."""
    # DEBUG_START
    thread_id = config.get("configurable", {}).get("thread_id", "cli")
    print(f"\n{'═' * 60}")
    print(f"[call_model] ▶ ENTER  thread={thread_id[:8]}  history_len={len(state['messages'])}")
    for i, m in enumerate(state["messages"]):
        role = type(m).__name__
        preview = str(m.content)[:100].replace("\n", " ")
        print(f"[call_model]   msg[{i}] {role}: {preview}")
    # DEBUG_END

    _check_cancel(config, "call_model")

    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]

    # DEBUG_START
    print(f"[call_model] → invoking LLM ({len(messages)} messages incl. system prompt) …")
    # DEBUG_END

    response = llm_with_tools.invoke(messages)

    # DEBUG_START
    if isinstance(response, AIMessage) and response.tool_calls:
        print(f"[call_model] ◀ LLM wants {len(response.tool_calls)} tool call(s):")
        for tc in response.tool_calls:
            print(f"[call_model]     tool={tc['name']}  args={tc['args']}")
    else:
        preview = str(response.content)[:120].replace("\n", " ")
        print(f"[call_model] ◀ LLM text response: {preview}")
    # DEBUG_END

    return {"messages": [response]}


async def pre_tool_guard(state: MessagesState, config: RunnableConfig) -> dict:
    """
    Pre-Tool Guard node — parameter validation with state look-back.

    Pass 1 — param check:
      Inspect every tool_call on the latest AIMessage. If all required
      parameters are present and non-empty, return {} and let
      route_after_guard forward to call_tools.

    Pass 2 — state look-back (self-correction):
      If any required parameter is missing, scan the conversation history
      using a targeted LLM extraction call to find values the user already
      provided in earlier messages.

      • All missing values found in history → patch the tool_call args
        in-place (same message id) and proceed to call_tools.
        A self-correction is logged for auditability.

      • Some values still missing after extraction → ask the user only for
        the remaining missing information. The clarification question
        replaces the tool-call AIMessage (same id, no tool_calls) so the
        checkpoint never contains dangling unexecuted tool calls.
    """
    # DEBUG_START
    thread_id = config.get("configurable", {}).get("thread_id", "cli")
    last = state["messages"][-1]
    tool_names = [tc["name"] for tc in last.tool_calls] if isinstance(last, AIMessage) else []
    print(f"[pre_tool_guard] ▶ ENTER  thread={thread_id[:8]}  checking {len(tool_names)} call(s): {tool_names}")
    # DEBUG_END

    _check_cancel(config, "pre_tool_guard")

    last = state["messages"][-1]
    assert isinstance(last, AIMessage) and last.tool_calls, (
        "pre_tool_guard invoked without tool_calls on the last message"
    )

    # ── Pass 1: collect missing param keys and labels ──────────────────────
    missing_keys: list[str] = []
    missing_labels: list[str] = []
    seen_keys: set[str] = set()

    for tc in last.tool_calls:
        required = _TOOL_REQUIRED_PARAMS.get(tc["name"], [])
        # DEBUG_START
        print(f"[pre_tool_guard]   tool={tc['name']}  required={required}  provided={list(tc['args'].keys())}")
        # DEBUG_END
        for param in required:
            val = tc["args"].get(param)
            if not val or (isinstance(val, str) and not val.strip()):
                if param not in seen_keys:
                    seen_keys.add(param)
                    missing_keys.append(param)
                    missing_labels.append(_PARAM_LABELS.get(param, param))

    if not missing_keys:
        # DEBUG_START
        print("[pre_tool_guard] ✓ all required params present — routing to call_tools")
        # DEBUG_END
        return {}

    # ── Pass 2: state look-back ────────────────────────────────────────────
    # DEBUG_START
    print(f"[pre_tool_guard] ✗ missing: {missing_keys} — scanning conversation history …")
    # DEBUG_END

    # Exclude the current AIMessage (last) from the extraction context.
    history = state["messages"][:-1]
    extracted = await _extract_params_from_history(history, missing_keys)
    filled   = {k: v for k, v in extracted.items() if v}
    still_missing_keys   = [k for k in missing_keys   if k not in filled]
    still_missing_labels = [l for k, l in zip(missing_keys, missing_labels) if k not in filled]

    # DEBUG_START
    if filled:
        print(f"[pre_tool_guard] [SELF-CORRECTION] extracted from history: {filled}")
    else:
        print("[pre_tool_guard] [SELF-CORRECTION] nothing found in history")
    # DEBUG_END

    if filled and not still_missing_keys:
        # All missing params recovered — patch tool_calls and proceed.
        patched_tool_calls = []
        for tc in last.tool_calls:
            new_args = dict(tc["args"])
            for key, value in filled.items():
                if not new_args.get(key):
                    new_args[key] = value
            patched_tool_calls.append({**tc, "args": new_args})

        patched_msg = AIMessage(
            content=last.content,
            tool_calls=patched_tool_calls,
            id=last.id,
        )

        logger.info(
            "[SELF-CORRECTION] thread=%s  patched %s with %s — retrying tool call",
            thread_id[:8], tool_names, filled,
        )
        # DEBUG_START
        print(f"[pre_tool_guard] [SELF-CORRECTION] patched args: {patched_tool_calls}")
        print("[pre_tool_guard] [SELF-CORRECTION] retrying tool call → routing to call_tools")
        # DEBUG_END

        return {"messages": [patched_msg]}

    # Some params still missing — ask the user only for what remains.
    labels_to_ask = still_missing_labels if still_missing_labels else missing_labels
    if len(labels_to_ask) == 1:
        question = (
            f"To help you, I need {labels_to_ask[0]}. "
            "Could you please provide it?"
        )
    else:
        items = ", ".join(labels_to_ask[:-1]) + f", and {labels_to_ask[-1]}"
        question = (
            f"To help you, I still need the following details: {items}. "
            "Could you please provide them?"
        )

    # DEBUG_START
    print(f"[pre_tool_guard] still missing after look-back: {still_missing_keys or missing_keys}")
    print(f"[pre_tool_guard]   clarifying question: {question}")
    print(f"[pre_tool_guard]   replacing AIMessage in-place (id={last.id}) → routing to END")
    # DEBUG_END

    return {"messages": [AIMessage(content=question, id=last.id)]}


async def call_tools_with_timeout(state: MessagesState, config: RunnableConfig) -> dict:
    """
    Execute each pending tool call.

    Each call runs in a thread-pool executor and is guarded by TOOL_TIMEOUT_SECS.
    Cancellation is checked before every individual tool execution.
    On timeout the ToolMessage carries MSG_TOOL_TIMEOUT so the LLM can relay
    a polite explanation to the user instead of crashing.
    """
    # DEBUG_START
    thread_id = config.get("configurable", {}).get("thread_id", "cli")
    last_msg = state["messages"][-1]
    n_tools = len(last_msg.tool_calls) if isinstance(last_msg, AIMessage) else 0
    print(f"[call_tools] ▶ ENTER  thread={thread_id[:8]}  executing {n_tools} tool(s)")
    # DEBUG_END

    _check_cancel(config, "call_tools entry")

    last_msg = state["messages"][-1]
    assert isinstance(last_msg, AIMessage) and last_msg.tool_calls, (
        "call_tools_with_timeout invoked without tool_calls on the last message"
    )

    loop = asyncio.get_running_loop()
    results: list[ToolMessage] = []

    for i, tc in enumerate(last_msg.tool_calls):
        # DEBUG_START
        print(f"[call_tools]   [{i+1}/{n_tools}] checking cancel before tool '{tc['name']}' …")
        # DEBUG_END
        _check_cancel(config, f"before tool '{tc['name']}'")

        tool = _tool_map.get(tc["name"])

        if tool is None:
            content = f"Unknown tool requested: {tc['name']}"
            # DEBUG_START
            print(f"[call_tools]   [{i+1}/{n_tools}] ✗ unknown tool '{tc['name']}'")
            # DEBUG_END
        else:
            # DEBUG_START
            print(f"[call_tools]   [{i+1}/{n_tools}] → {tc['name']}  args={tc['args']}")
            # DEBUG_END
            try:
                raw = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        lambda t=tool, a=tc["args"]: t.invoke(a),
                    ),
                    timeout=TOOL_TIMEOUT_SECS,
                )
                content = json.dumps(raw) if isinstance(raw, dict) else str(raw)
                # DEBUG_START
                preview = content[:300].replace("\n", " ")
                print(f"[call_tools]   [{i+1}/{n_tools}] ✓ result ({len(content)} chars): {preview}{'…' if len(content) > 300 else ''}")
                # DEBUG_END
            except asyncio.TimeoutError:
                content = MSG_TOOL_TIMEOUT
                # DEBUG_START
                print(f"[call_tools]   [{i+1}/{n_tools}] ✗ TIMEOUT after {TOOL_TIMEOUT_SECS}s")
                # DEBUG_END
            except Exception as exc:
                content = f"Tool error: {exc}"
                # DEBUG_START
                print(f"[call_tools]   [{i+1}/{n_tools}] ✗ ERROR: {exc}")
                # DEBUG_END

        results.append(
            ToolMessage(
                content=content,
                tool_call_id=tc["id"],
                name=tc["name"],
            )
        )

    # DEBUG_START
    print(f"[call_tools] ◀ done — {len(results)} ToolMessage(s) returned")
    # DEBUG_END

    return {"messages": results}


# ---------------------------------------------------------------------------
# Conditional edge routers
# ---------------------------------------------------------------------------

def route_after_model(state: MessagesState) -> Literal["pre_tool_guard", "__end__"]:
    """Route to Pre-Tool Guard when the LLM produced tool calls, else END."""
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        # DEBUG_START
        print(f"[route_after_model] → pre_tool_guard  ({len(last.tool_calls)} tool call(s) pending)")
        # DEBUG_END
        return "pre_tool_guard"
    # DEBUG_START
    print("[route_after_model] → END  (plain text — no tool calls)")
    # DEBUG_END
    return END


def route_after_guard(state: MessagesState) -> Literal["call_tools", "__end__"]:
    """
    Route based on what pre_tool_guard returned.

    • Returned {} or patched AIMessage (still has tool_calls) → call_tools.
    • Returned clarification AIMessage (no tool_calls)         → END.
    """
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        # DEBUG_START
        print("[route_after_guard] → call_tools  (params validated / self-corrected)")
        # DEBUG_END
        return "call_tools"
    # DEBUG_START
    print("[route_after_guard] → END  (guard emitted clarifying question)")
    # DEBUG_END
    return END


# ---------------------------------------------------------------------------
# Graph factory
# ---------------------------------------------------------------------------

def get_agent_graph(checkpointer=None):
    """
    Build and compile the ReAct graph with a Pre-Tool Guard.

    Flow:
      START
        → call_model          (LLM invocation)
        → route_after_model   (tool_calls? → pre_tool_guard : END)
        → pre_tool_guard      (param check → state look-back → patch/ask)
        → route_after_guard   (tool_calls still present? → call_tools : END)
        → call_tools          (timeout-protected async execution)
        → call_model          (next turn)

    Cancellation is checked at the entry of every node via _check_cancel(config).
    """
    workflow = StateGraph(MessagesState)

    workflow.add_node("call_model",     call_model)
    workflow.add_node("pre_tool_guard", pre_tool_guard)
    workflow.add_node("call_tools",     call_tools_with_timeout)

    workflow.add_edge(START, "call_model")
    workflow.add_conditional_edges("call_model",     route_after_model)
    workflow.add_conditional_edges("pre_tool_guard", route_after_guard)
    workflow.add_edge("call_tools", "call_model")

    return workflow.compile(checkpointer=checkpointer)


# Stateless default graph — used by the CLI and tests.
graph = get_agent_graph()


# ---------------------------------------------------------------------------
# Local interactive CLI
# ---------------------------------------------------------------------------

async def _cli_main() -> None:
    print("Travel Agent ready. Type 'exit' or 'quit' to stop.\n")
    history: list = []
    cli_config = {"recursion_limit": RECURSION_LIMIT}

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break

        history.append(HumanMessage(content=user_input))

        result = await graph.ainvoke({"messages": history}, config=cli_config)

        new_messages = result["messages"][len(history):]
        history = result["messages"]

        for msg in new_messages:
            if isinstance(msg, AIMessage):
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        print(f"\n  [Tool Call] {tc['name']} -> {tc['args']}")
                else:
                    print(f"\nAgent: {msg.content}\n")
            elif isinstance(msg, ToolMessage):
                preview = str(msg.content)
                if len(preview) > 300:
                    preview = preview[:300] + "..."
                print(f"  [Tool Result] {preview}")


if __name__ == "__main__":
    asyncio.run(_cli_main())
