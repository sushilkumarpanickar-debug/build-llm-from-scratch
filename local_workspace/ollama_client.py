import json
from urllib.request import Request, urlopen

OLLAMA_URL = "http://127.0.0.1:11434/api/"


def request(path, body=None, timeout=None):
    req = Request(
        OLLAMA_URL + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json"},
    )
    with urlopen(req, timeout=timeout or (180 if body else 3)) as response:
        return json.load(response)


def models():
    try:
        result = []
        for model in request("tags").get("models", []):
            name = model.get("name", "")
            if name and "cloud" not in name.lower() and not model.get("remote_host"):
                result.append(name)
        return result
    except Exception:
        return []


def chat_models():
    return [name for name in models() if not name.startswith(("nomic-embed", "mxbai-embed", "all-minilm"))]


def choose_chat_model(preferred=None):
    available = chat_models()
    if preferred in available:
        return preferred
    for candidate in ("qwen3:8b", "qwen2.5:7b", "qwen2.5:3b"):
        if candidate in available:
            return candidate
    return available[0] if available else None


def embed(texts, model="nomic-embed-text"):
    if isinstance(texts, str):
        texts = [texts]
    result = request("embed", {"model": model, "input": texts}, timeout=180)
    vectors = result.get("embeddings")
    if not vectors:
        raise RuntimeError("Ollama returned no embeddings")
    return vectors


def chat(model, messages, num_predict=900):
    result = request(
        "chat",
        {"model": model, "messages": messages, "stream": False, "options": {"num_predict": num_predict}},
        timeout=300,
    )
    answer = result.get("message", {}).get("content", "").strip()
    if not answer:
        raise RuntimeError("The local model returned an empty response")
    return answer
