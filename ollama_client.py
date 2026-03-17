import requests

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "mistral"


class OllamaError(Exception):
    """Raised when the Ollama API returns an error or is unreachable."""


def chat(messages: list[dict], model: str = DEFAULT_MODEL) -> str:
    """
    Send a chat request to the local Ollama instance.

    Args:
        messages: List of {'role': ..., 'content': ...} dicts.
        model:    Ollama model name to use.

    Returns:
        The assistant's reply as a plain string.

    Raises:
        OllamaError: If the request fails or the API returns an error.
    """
    url = f"{OLLAMA_BASE_URL}/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
    }

    try:
        response = requests.post(url, json=payload, timeout=60)
    except requests.exceptions.ConnectionError:
        raise OllamaError(
            "Could not connect to Ollama. Make sure it is running on localhost:11434."
        )
    except requests.exceptions.Timeout:
        raise OllamaError("Ollama request timed out after 60 seconds.")

    if response.status_code != 200:
        raise OllamaError(
            f"Ollama returned HTTP {response.status_code}: {response.text}"
        )

    data = response.json()
    try:
        return data["message"]["content"]
    except (KeyError, TypeError) as exc:
        raise OllamaError(f"Unexpected response format from Ollama: {data}") from exc


def is_available(model: str = DEFAULT_MODEL) -> bool:
    """
    Quick health-check: verify Ollama is running and the model is available.

    Returns:
        True if the model is listed, False otherwise.
    """
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code != 200:
            return False
        models = [m["name"] for m in response.json().get("models", [])]
        return any(m.startswith(model) for m in models)
    except requests.exceptions.RequestException:
        return False
