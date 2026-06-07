import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.errors import GraphRecursionError
from psycopg_pool import AsyncConnectionPool
from pydantic import BaseModel

from app.agent import get_agent_graph, TaskCancelled
from app.db import (
    setup_token_table,
    setup_cancellation_table,
    get_thread_tokens,
    add_thread_tokens,
    clear_thread_data,
    log_cancellation,
)
from app.safety import (
    RECURSION_LIMIT,
    TOKEN_BUDGET,
    MSG_RECURSION,
    MSG_BUDGET_EXCEEDED,
    MSG_CANCELLED,
    validate_user_input,
)
from app.session_store import session_store

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App state (populated during lifespan startup)
# ---------------------------------------------------------------------------

_pool: AsyncConnectionPool | None = None
_graph = None


# ---------------------------------------------------------------------------
# Lifespan — DB pool + checkpointer + table setup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _pool, _graph

    db_url = os.environ["DATABASE_URL"]

    _pool = AsyncConnectionPool(
        conninfo=db_url,
        max_size=20,
        kwargs={"autocommit": True, "prepare_threshold": 0},
        open=False,
    )
    await _pool.open()

    checkpointer = AsyncPostgresSaver(_pool)
    await checkpointer.setup()              # LangGraph checkpoint tables
    await setup_token_table(_pool)          # token-usage table
    await setup_cancellation_table(_pool)   # cancellation audit-log table

    _graph = get_agent_graph(checkpointer=checkpointer)

    yield

    await _pool.close()


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(title="Travel Agent API", version="0.1.0", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    thread_id: str
    user_message: str


class ClearRequest(BaseModel):
    thread_id: str


class CancelRequest(BaseModel):
    thread_id: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/chat/clear")
async def chat_clear(request: ClearRequest):
    """
    Delete all Postgres state for the given thread_id.
    Called by the frontend when the user starts a new chat session.
    """
    if _pool is None:
        raise HTTPException(status_code=503, detail="Agent not initialised yet")
    await clear_thread_data(_pool, request.thread_id)
    return {"status": "cleared", "thread_id": request.thread_id}


@app.get("/chat/history")
async def chat_history(thread_id: str):
    """
    Return the stored message list for a thread as display-ready JSON.

    Reads directly from the LangGraph checkpoint — no LLM call, no token cost.
    Returns an empty list if the thread has never been used.

    Each item has the shape:
      {"type": "user"|"assistant"|"tool_call"|"tool_result",
       "content": "...",
       "tool": "..." | null}
    """
    if _graph is None:
        raise HTTPException(status_code=503, detail="Agent not initialised yet")

    config = {"configurable": {"thread_id": thread_id}}
    state = await _graph.aget_state(config)
    messages = state.values.get("messages", []) if state and state.values else []
    return _history_to_json(messages)


@app.get("/chat/sessions")
async def chat_sessions():
    """
    Return all chat sessions (unique thread_ids) with titles extracted from
    the first HumanMessage in each thread.
    Sorted newest-first using thread_token_usage.updated_at.
    Cost: $0 — no LLM calls. Pure DB reads, concurrent per thread.
    """
    if _pool is None or _graph is None:
        raise HTTPException(status_code=503, detail="Agent not initialised yet")

    async with _pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT c.thread_id, t.updated_at
                FROM (
                    SELECT DISTINCT thread_id
                    FROM checkpoints
                    WHERE checkpoint_ns = ''
                ) c
                LEFT JOIN thread_token_usage t ON c.thread_id = t.thread_id
                ORDER BY t.updated_at DESC NULLS LAST
            """)
            rows = await cur.fetchall()

    if not rows:
        return []

    async def _session_info(thread_id: str, updated_at) -> dict:
        try:
            config = {"configurable": {"thread_id": thread_id}}
            state = await _graph.aget_state(config)
            messages = state.values.get("messages", []) if state and state.values else []
            title = "Chat Session"
            for msg in messages:
                if isinstance(msg, HumanMessage):
                    raw = str(msg.content).strip()
                    title = (raw[:60] + "…") if len(raw) > 60 else raw or "Chat Session"
                    break
        except Exception:
            title = "Chat Session"
            updated_at = None
        return {
            "thread_id": thread_id,
            "title": title,
            "updated_at": updated_at.isoformat() if updated_at else None,
        }

    results = await asyncio.gather(*[
        _session_info(row[0], row[1]) for row in rows
    ])
    return list(results)


@app.post("/chat/cancel")
async def chat_cancel(request: CancelRequest):
    """
    Set the cancellation flag for an active streaming request.

    The next time the agent enters call_model or call_tools it will raise
    TaskCancelled, immediately stopping all server-side LLM/tool work.
    The cancellation event is logged to the database for auditability.
    """
    found = session_store.cancel_thread(request.thread_id)
    return {
        "status": "cancelled" if found else "not_found",
        "thread_id": request.thread_id,
    }


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream agent responses as Server-Sent Events.

    Pre-flight checks (respond immediately without hitting the LLM):
      1. Input validation   — rejects injection patterns / oversized input
      2. Budget guard       — rejects threads that exceeded TOKEN_BUDGET

    SSE event types:
      {"type": "tool_call",   "tool": "...", "input": {...}}
      {"type": "tool_result", "tool": "...", "output": "..."}
      {"type": "token",       "content": "..."}
      {"type": "done"}
      {"type": "error",       "message": "..."}   ← unhandled exceptions only
    """
    if _graph is None:
        raise HTTPException(status_code=503, detail="Agent not initialised yet")

    async def event_generator():
        # ── 1. Input validation ────────────────────────────────────────────
        validation_error = validate_user_input(request.user_message)
        if validation_error:
            yield _agent_msg(validation_error)
            yield _done()
            return

        # ── 2. Budget guard ────────────────────────────────────────────────
        current_tokens = await get_thread_tokens(_pool, request.thread_id)
        if current_tokens >= TOKEN_BUDGET:
            logger.warning(
                "Thread %s exceeded token budget (%d >= %d)",
                request.thread_id, current_tokens, TOKEN_BUDGET,
            )
            yield _agent_msg(MSG_BUDGET_EXCEEDED)
            yield _done()
            return

        # ── 3. Register cancellation event for this thread ─────────────────
        session_store.create(request.thread_id)

        config = {
            "configurable": {"thread_id": request.thread_id},
            "recursion_limit": RECURSION_LIMIT,
        }
        initial_state = {"messages": [HumanMessage(content=request.user_message)]}
        session_tokens = 0
        was_cancelled = False

        try:
            async for event in _graph.astream_events(
                initial_state, config=config, version="v2"
            ):
                kind = event["event"]
                node = event.get("metadata", {}).get("langgraph_node", "")

                # ── Token counting ─────────────────────────────────────
                if kind == "on_chat_model_end" and node == "call_model":
                    output = event["data"].get("output")
                    if output and hasattr(output, "usage_metadata") and output.usage_metadata:
                        session_tokens += (
                            (output.usage_metadata.get("input_tokens") or 0)
                            + (output.usage_metadata.get("output_tokens") or 0)
                        )

                # ── Pre-Tool Guard emitted a clarifying question ────────
                elif kind == "on_chain_end" and node == "pre_tool_guard":
                    output = event["data"].get("output") or {}
                    if isinstance(output, dict):
                        for msg in output.get("messages", []):
                            if (
                                isinstance(msg, AIMessage)
                                and isinstance(msg.content, str)
                                and msg.content.strip()
                            ):
                                yield _sse(json.dumps({
                                    "type": "token",
                                    "content": msg.content,
                                }))

                # ── Tool invocation started ────────────────────────────
                elif kind == "on_tool_start" and node == "call_tools":
                    yield _sse(json.dumps({
                        "type": "tool_call",
                        "tool": event["name"],
                        "input": event["data"].get("input", {}),
                    }))

                # ── Tool returned a result ─────────────────────────────
                elif kind == "on_tool_end" and node == "call_tools":
                    output = event["data"].get("output", "")
                    if isinstance(output, ToolMessage):
                        output = output.content
                    yield _sse(json.dumps({
                        "type": "tool_result",
                        "tool": event["name"],
                        "output": str(output),
                    }))

                # ── LLM streaming a text token ─────────────────────────
                elif kind == "on_chat_model_stream" and node == "call_model":
                    chunk = event["data"]["chunk"]
                    text = _extract_text(chunk.content)
                    if text:
                        yield _sse(json.dumps({"type": "token", "content": text}))

            yield _done()

        except TaskCancelled:
            was_cancelled = True
            logger.info("Stream cancelled for thread %s", request.thread_id)
            yield _agent_msg(MSG_CANCELLED)
            yield _done()

        except GraphRecursionError:
            logger.warning("Recursion limit hit for thread %s", request.thread_id)
            yield _agent_msg(MSG_RECURSION)
            yield _done()

        except Exception as exc:
            logger.exception("Unhandled error in stream for thread %s", request.thread_id)
            yield _sse(json.dumps({"type": "error", "message": str(exc)}))

        finally:
            # Always deregister the cancel event.
            session_store.clear_session(request.thread_id)

            # Persist cancellation audit record if applicable.
            if was_cancelled and _pool is not None:
                await log_cancellation(_pool, request.thread_id)

            # Persist token usage regardless of how the stream ended.
            if session_tokens > 0 and _pool is not None:
                await add_thread_tokens(_pool, request.thread_id, session_tokens)
                logger.info(
                    "Thread %s used %d tokens this turn (%d cumulative)",
                    request.thread_id,
                    session_tokens,
                    current_tokens + session_tokens,
                )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# SSE helpers
# ---------------------------------------------------------------------------

def _sse(payload: str) -> str:
    return f"data: {payload}\n\n"

def _done() -> str:
    return _sse(json.dumps({"type": "done"}))

def _agent_msg(text: str) -> str:
    """Emit a message that renders as an assistant bubble on the frontend."""
    return _sse(json.dumps({"type": "token", "content": text}))


# ---------------------------------------------------------------------------
# History serialisation helper
# ---------------------------------------------------------------------------

def _history_to_json(messages: list) -> list[dict]:
    """
    Convert a LangChain message list (from a checkpoint) to the same JSON
    shape the frontend already understands for live SSE events.

    HumanMessage  → type "user"
    AIMessage     → type "tool_call" (one entry per tool call) or "assistant"
    ToolMessage   → type "tool_result"
    """
    result: list[dict] = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            result.append({"type": "user", "content": str(msg.content)})

        elif isinstance(msg, AIMessage):
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    result.append({
                        "type": "tool_call",
                        "content": json.dumps(tc["args"], indent=2),
                        "tool": tc["name"],
                    })
            elif msg.content:
                text = _extract_text(msg.content)
                if text:
                    result.append({"type": "assistant", "content": text})

        elif isinstance(msg, ToolMessage):
            content = msg.content
            try:
                content = json.dumps(json.loads(content), indent=2)
            except Exception:
                pass
            result.append({
                "type": "tool_result",
                "content": content,
                "tool": msg.name or "",
            })
    return result


# ---------------------------------------------------------------------------
# Text extraction helper
# ---------------------------------------------------------------------------

def _extract_text(content) -> str:
    """
    Extract plain text from an Anthropic streaming chunk's content field.
    Tool-call blocks are skipped (they surface via on_tool_start/on_tool_end).
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
        return "".join(parts)
    return ""
