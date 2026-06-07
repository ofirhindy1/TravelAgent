"""
Thread-scoped cancellation flags.

Each active streaming request registers an asyncio.Event under its thread_id.
Calling cancel_thread(thread_id) sets the event; the agent loop calls
get_cancel_event(thread_id).is_set() before every LLM/tool invocation so
server-side work stops at the next safe checkpoint.
"""
import asyncio


class SessionStore:
    """In-process store of per-thread cancellation events."""

    def __init__(self) -> None:
        self._events: dict[str, asyncio.Event] = {}

    def create(self, thread_id: str) -> asyncio.Event:
        """Register a fresh (unset) cancellation event for *thread_id*."""
        event = asyncio.Event()
        self._events[thread_id] = event
        return event

    def get_cancel_event(self, thread_id: str) -> asyncio.Event | None:
        """Return the cancellation event for *thread_id*, or None if not registered."""
        return self._events.get(thread_id)

    def cancel_thread(self, thread_id: str) -> bool:
        """
        Set the cancellation flag for *thread_id*.
        Returns True if the thread was active, False if it was not found.
        """
        event = self._events.get(thread_id)
        if event:
            event.set()
            return True
        return False

    def clear_session(self, thread_id: str) -> None:
        """Deregister the event. Call from the finally block of event_generator."""
        self._events.pop(thread_id, None)


# Single process-wide instance shared by all request handlers.
session_store = SessionStore()
