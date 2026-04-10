from __future__ import annotations

import math
import re

from .embeddings import _mock_embed


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])(?:\s+|\n+)", text.strip())
            if sentence.strip()
        ]

        if not sentences:
            return [text.strip()]

        chunks: list[str] = []
        for start in range(0, len(sentences), self.max_sentences_per_chunk):
            group = sentences[start : start + self.max_sentences_per_chunk]
            chunks.append(" ".join(group).strip())
        return chunks


class SemanticChunker:
    """
    Group adjacent sentences by semantic similarity.

    The chunker starts a new chunk when the similarity between the current
    chunk embedding and the next sentence embedding drops below the threshold
    or when the chunk would exceed max_chunk_size.
    """

    def __init__(
        self,
        similarity_threshold: float = 0.72,
        max_chunk_size: int = 500,
    ) -> None:
        self.similarity_threshold = similarity_threshold
        self.max_chunk_size = max(1, max_chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        blocks = self._build_blocks(text.strip())
        if not blocks:
            return [text.strip()]

        chunks: list[str] = []
        current_blocks: list[str] = []
        current_embedding: list[float] | None = None

        for block in blocks:
            block_embedding = _mock_embed(block)
            candidate_blocks = current_blocks + [block]
            candidate_text = "\n\n".join(candidate_blocks).strip()

            if not current_blocks:
                current_blocks = [block]
                current_embedding = block_embedding
                continue

            assert current_embedding is not None
            similarity = compute_similarity(current_embedding, block_embedding)

            if similarity >= self.similarity_threshold and len(candidate_text) <= self.max_chunk_size:
                current_blocks.append(block)
                current_embedding = _mock_embed("\n\n".join(current_blocks))
            else:
                chunks.append("\n\n".join(current_blocks).strip())
                current_blocks = [block]
                current_embedding = block_embedding

        if current_blocks:
            chunks.append("\n\n".join(current_blocks).strip())

        return chunks

    def _build_blocks(self, text: str) -> list[str]:
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n+", text) if part.strip()]
        blocks: list[str] = []
        pending_prefix: list[str] = []

        for paragraph in paragraphs:
            if self._is_structural_block(paragraph):
                if len(paragraph) <= self.max_chunk_size // 2:
                    pending_prefix = [paragraph]
                else:
                    blocks.extend(self._split_long_block(paragraph))
                continue

            if pending_prefix:
                paragraph = "\n\n".join(pending_prefix + [paragraph]).strip()
                pending_prefix = []

            if len(paragraph) <= self.max_chunk_size:
                blocks.append(paragraph)
                continue

            sentences = [
                sentence.strip()
                for sentence in re.split(r"(?<=[.!?])(?:\s+|\n+)", paragraph)
                if sentence.strip()
            ]

            if len(sentences) <= 1:
                blocks.extend(self._split_long_block(paragraph))
            else:
                blocks.extend(self._pack_sentences(sentences))

        if pending_prefix:
            blocks.extend(pending_prefix)

        return [block for block in blocks if block]

    def _is_structural_block(self, paragraph: str) -> bool:
        lines = paragraph.splitlines()
        if len(lines) > 1:
            return True
        line = paragraph.strip()
        return bool(
            re.match(r"^(#{1,6}\s+|[-*+]\s+|\d+(\.\d+)*\.\s+)", line)
            or re.match(r"^\d+\.$", line)
        )

    def _pack_sentences(self, sentences: list[str]) -> list[str]:
        blocks: list[str] = []
        current_sentences: list[str] = []
        current_embedding: list[float] | None = None

        for sentence in sentences:
            sentence_embedding = _mock_embed(sentence)
            if not current_sentences:
                current_sentences = [sentence]
                current_embedding = sentence_embedding
                continue

            assert current_embedding is not None
            candidate_text = " ".join(current_sentences + [sentence]).strip()
            similarity = compute_similarity(current_embedding, sentence_embedding)

            if similarity >= self.similarity_threshold and len(candidate_text) <= self.max_chunk_size:
                current_sentences.append(sentence)
                current_embedding = _mock_embed(" ".join(current_sentences))
            else:
                blocks.append(" ".join(current_sentences).strip())
                current_sentences = [sentence]
                current_embedding = sentence_embedding

        if current_sentences:
            blocks.append(" ".join(current_sentences).strip())

        return blocks

    def _split_long_block(self, block: str) -> list[str]:
        if len(block) <= self.max_chunk_size:
            return [block]
        return [
            block[start : start + self.max_chunk_size].strip()
            for start in range(0, len(block), self.max_chunk_size)
            if block[start : start + self.max_chunk_size].strip()
        ]


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        pieces = self._split(text, self.separators)
        return [piece.strip() for piece in pieces if piece and piece.strip()]

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        stripped = current_text.strip()
        if not stripped:
            return []
        if len(stripped) <= self.chunk_size:
            return [stripped]
        if not remaining_separators:
            return [
                stripped[start : start + self.chunk_size]
                for start in range(0, len(stripped), self.chunk_size)
            ]

        separator = remaining_separators[0]
        rest = remaining_separators[1:]

        if separator == "":
            return [
                stripped[start : start + self.chunk_size]
                for start in range(0, len(stripped), self.chunk_size)
            ]

        raw_parts = stripped.split(separator)
        if len(raw_parts) == 1:
            return self._split(stripped, rest)

        parts = []
        for index, part in enumerate(raw_parts):
            if index < len(raw_parts) - 1:
                parts.append(part + separator)
            elif part:
                parts.append(part)

        chunks: list[str] = []
        current_chunk = ""

        for part in parts:
            piece = part.strip()
            if not piece:
                continue

            if len(piece) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                chunks.extend(self._split(piece, rest))
                continue

            candidate = f"{current_chunk}{piece}" if current_chunk else piece
            if len(candidate) <= self.chunk_size:
                current_chunk = candidate
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = piece

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    mag_a = math.sqrt(_dot(vec_a, vec_a))
    mag_b = math.sqrt(_dot(vec_b, vec_b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return _dot(vec_a, vec_b) / (mag_a * mag_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=max(0, chunk_size // 10)),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=max(1, chunk_size // 100)),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }

        comparison: dict[str, dict] = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            count = len(chunks)
            avg_length = (sum(len(chunk) for chunk in chunks) / count) if count else 0.0
            comparison[name] = {
                "count": count,
                "avg_length": avg_length,
                "chunks": chunks,
            }

        return comparison
