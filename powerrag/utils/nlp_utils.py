import tiktoken

encoder = tiktoken.get_encoding("cl100k_base")

def num_tokens_from_string(text: str) -> int:
    """Calculate token count for text using tiktoken BPE tokenizer."""
    try:
        return len(encoder.encode(text))
    except Exception:
        return 0