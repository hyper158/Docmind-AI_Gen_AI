import re
from typing import List

# Standard conservative heuristic: 1 token ≈ 4 characters (or ~0.75 words)
CHARS_PER_TOKEN = 4.0


def estimate_token_count(text: str) -> int:
    """Estimates the number of tokens in a string using word and character heuristics."""
    if not text:
        return 0
    # Average between character-based and whitespace word-based count for robustness
    char_estimate = len(text) / CHARS_PER_TOKEN
    word_estimate = len(text.split()) * 1.3
    return max(1, int((char_estimate + word_estimate) / 2))


def split_text_into_token_chunks(
    text: str,
    max_chunk_chars: int = 3000,
    overlap_chars: int = 300,
) -> List[str]:
    """
    Splits text into token-budgeted chunks respecting sentence boundaries.
    Ensures long pages are never summarized using only their beginning.
    """
    if len(text) <= max_chunk_chars:
        return [text]

    # Split on paragraph or sentence boundaries
    sentences = re.split(r"(?<=[.?!;\n])\s+", text)
    chunks: List[str] = []
    current_chunk: List[str] = []
    current_length = 0

    for sentence in sentences:
        s_len = len(sentence)
        if current_length + s_len > max_chunk_chars and current_chunk:
            chunk_str = " ".join(current_chunk).strip()
            if chunk_str:
                chunks.append(chunk_str)

            # Keep overlap from the end of current_chunk
            overlap_acc = []
            overlap_len = 0
            for item in reversed(current_chunk):
                if overlap_len + len(item) <= overlap_chars:
                    overlap_acc.insert(0, item)
                    overlap_len += len(item)
                else:
                    break
            current_chunk = overlap_acc + [sentence]
            current_length = sum(len(x) for x in current_chunk) + len(current_chunk)
        else:
            current_chunk.append(sentence)
            current_length += s_len + 1

    if current_chunk:
        chunk_str = " ".join(current_chunk).strip()
        if chunk_str:
            chunks.append(chunk_str)

    # Fallback if sentence splitting produced nothing or a chunk is still too large
    if not chunks:
        step = max_chunk_chars - overlap_chars
        chunks = [text[i : i + max_chunk_chars] for i in range(0, len(text), step)]

    return chunks
