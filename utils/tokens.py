import tiktoken


_encoder = None


def _get_encoder():
    global _encoder
    if _encoder is None:
        _encoder = tiktoken.get_encoding("cl100k_base")
    return _encoder


def count_tokens(text: str) -> int:
    try:
        return len(_get_encoder().encode(text))
    except Exception:
        return len(text) // 4


def count_messages_tokens(messages: list[dict]) -> int:
    total = 0
    for msg in messages:
        total += count_tokens(msg.get("content", ""))
        total += 4  # role + formatting overhead
    return total
