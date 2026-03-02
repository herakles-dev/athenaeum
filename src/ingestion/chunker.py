"""Smart text chunking with semantic boundary detection."""

import re
import tiktoken


ENCODER = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    return len(ENCODER.encode(text))


def chunk_text(text: str, max_tokens: int = 500, overlap_tokens: int = 50) -> list[dict]:
    """Split text into chunks at sentence boundaries with token-based sizing.

    Returns list of dicts with 'text', 'token_count', 'chunk_index'.
    """
    # Split into paragraphs first, then sentences
    paragraphs = re.split(r'\n\s*\n', text.strip())
    sentences = []
    for para in paragraphs:
        # Split paragraph into sentences
        sents = re.split(r'(?<=[.!?])\s+', para.strip())
        sentences.extend(sents)
        sentences.append("")  # paragraph break marker

    chunks = []
    current_sentences = []
    current_tokens = 0

    for sent in sentences:
        sent_tokens = count_tokens(sent)

        # If a single sentence exceeds max, split it by words
        if sent_tokens > max_tokens:
            # Flush current
            if current_sentences:
                chunk_text_str = " ".join(s for s in current_sentences if s)
                if chunk_text_str.strip():
                    chunks.append({
                        "text": chunk_text_str.strip(),
                        "token_count": count_tokens(chunk_text_str),
                        "chunk_index": len(chunks)
                    })
                current_sentences = []
                current_tokens = 0

            # Split long sentence by words
            words = sent.split()
            word_chunk = []
            word_tokens = 0
            for word in words:
                wt = count_tokens(word + " ")
                if word_tokens + wt > max_tokens and word_chunk:
                    chunk_str = " ".join(word_chunk)
                    chunks.append({
                        "text": chunk_str,
                        "token_count": count_tokens(chunk_str),
                        "chunk_index": len(chunks)
                    })
                    word_chunk = []
                    word_tokens = 0
                word_chunk.append(word)
                word_tokens += wt
            if word_chunk:
                chunk_str = " ".join(word_chunk)
                chunks.append({
                    "text": chunk_str,
                    "token_count": count_tokens(chunk_str),
                    "chunk_index": len(chunks)
                })
            continue

        if current_tokens + sent_tokens > max_tokens and current_sentences:
            chunk_text_str = " ".join(s for s in current_sentences if s)
            if chunk_text_str.strip():
                chunks.append({
                    "text": chunk_text_str.strip(),
                    "token_count": count_tokens(chunk_text_str),
                    "chunk_index": len(chunks)
                })

            # Overlap: keep last few sentences that fit within overlap budget
            overlap_sents = []
            overlap_count = 0
            for s in reversed(current_sentences):
                st = count_tokens(s)
                if overlap_count + st > overlap_tokens:
                    break
                overlap_sents.insert(0, s)
                overlap_count += st

            current_sentences = overlap_sents
            current_tokens = overlap_count

        current_sentences.append(sent)
        current_tokens += sent_tokens

    # Flush remaining
    if current_sentences:
        chunk_text_str = " ".join(s for s in current_sentences if s)
        if chunk_text_str.strip():
            chunks.append({
                "text": chunk_text_str.strip(),
                "token_count": count_tokens(chunk_text_str),
                "chunk_index": len(chunks)
            })

    # Re-index
    for i, c in enumerate(chunks):
        c["chunk_index"] = i

    return chunks
