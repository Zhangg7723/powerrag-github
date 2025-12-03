import tiktoken

encoder = tiktoken.get_encoding("cl100k_base")

def num_tokens_from_string(text: str) -> int:
    """Calculate token count for text"""
    # Simple calculation: 1 token per ASCII character
    # 2 tokens for non-ASCII characters (Chinese, Japanese, Korean, etc.)
    total = 0
    for char in text:
        if ord(char) < 128:  # ASCII characters
            total += 1
        else:  # Non-ASCII characters (Chinese, Japanese, Korean, etc.)
            total += 2
    return total