class Session:
    """Tracks filter history for the current SharkAssist session."""

    def __init__(self):
        self._history: list[dict] = []  # Ollama chat-format messages
        self._filters: list[dict] = []  # Structured filter records

    def add_exchange(self, user_query: str, raw_response: str, parsed: dict):
        """
        Record a completed query/response exchange.

        Args:
            user_query:   The plain-English query the user submitted.
            raw_response: The raw text the model returned.
            parsed:       The structured dict from prompt_builder.parse_response().
        """
        self._history.append({"role": "user", "content": user_query})
        self._history.append({"role": "assistant", "content": raw_response})

        self._filters.append({
            "query": user_query,
            "filter": parsed["filter"],
            "explanation": parsed["explanation"],
            "next_steps": parsed["next_steps"],
        })

    def get_history(self) -> list[dict]:
        """Return chat history in Ollama message format."""
        return list(self._history)

    def get_filters(self) -> list[dict]:
        """Return all recorded filter records for this session."""
        return list(self._filters)

    def clear(self):
        """Reset the session."""
        self._history.clear()
        self._filters.clear()

    def __len__(self) -> int:
        return len(self._filters)
