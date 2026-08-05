"""
ChunkVectorStore — lightweight in-memory cosine similarity search.

Zero external dependencies (pure Python + math from stdlib).
Built from embedded chunks after Stage 3.5; queried during Stage 6
to retrieve the most semantically relevant chunks per documentation template.
"""
import math
from typing import List, Optional, Dict, Any


class ChunkVectorStore:
    """
    In-memory vector store for cosine similarity search over embedded chunks.

    Usage:
        store = ChunkVectorStore()
        store.build(chunks)           # chunks must have "embedding" key
        results = store.search(query_vector, top_k=8)
    """

    def __init__(self):
        self._vectors: List[List[float]] = []      # parallel list of embedding vectors
        self._chunks: List[Dict[str, Any]] = []    # parallel list of chunk metadata (no embedding key)
        self._dim: int = 0

    # ------------------------------------------------------------------
    # Building the index
    # ------------------------------------------------------------------

    def build(self, chunks: List[dict]) -> None:
        """
        Index all chunks that carry an "embedding" key.

        The stored copy strips the "embedding" key to keep memory lean.
        """
        self._vectors = []
        self._chunks = []

        for chunk in chunks:
            vec = chunk.get("embedding")
            if not vec:
                continue

            # Normalise the vector once at index time for faster cosine search
            norm_vec = _normalise(vec)
            if norm_vec is None:
                continue

            self._vectors.append(norm_vec)

            # Store a lightweight copy — drop raw content and embedding to save RAM
            slim = {k: v for k, v in chunk.items() if k not in ("embedding", "content")}
            self._chunks.append(slim)

        if self._vectors:
            self._dim = len(self._vectors[0])

        print(f"[VectorStore] Indexed {len(self._vectors)} / {len(chunks)} chunks.")

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------

    def is_built(self) -> bool:
        """Return True if the store has at least one indexed chunk."""
        return len(self._vectors) > 0

    def search(
        self,
        query_vector: List[float],
        top_k: int = 8,
    ) -> List[Dict[str, Any]]:
        """
        Return the top_k most similar chunk metadata dicts.

        Args:
            query_vector: Raw (unnormalised) query embedding from the same model.
            top_k:        Number of results to return.

        Returns:
            List of chunk dicts (without "embedding" or "content" keys) sorted
            by descending cosine similarity.  May be shorter than top_k if the
            store contains fewer chunks.
        """
        if not self._vectors:
            return []

        norm_q = _normalise(query_vector)
        if norm_q is None:
            return []

        # Dot product against pre-normalised index vectors = cosine similarity
        scores = [_dot(norm_q, v) for v in self._vectors]

        # Pair with indices, sort descending, take top_k
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        top = ranked[:top_k]

        return [self._chunks[idx] for idx, _score in top]

    def search_by_text_embedding(
        self,
        embedder,          # AzureEmbedder instance
        query_text: str,
        top_k: int = 8,
    ) -> List[Dict[str, Any]]:
        """
        Convenience wrapper: embed `query_text` then call search().

        Returns empty list (not an exception) if embedding fails.
        """
        try:
            vectors = embedder.embed_texts([query_text])
            if not vectors or vectors[0] is None:
                return []
            return self.search(vectors[0], top_k=top_k)
        except Exception as e:
            print(f"[VectorStore] Query embedding failed: {e} — skipping RAG for this template.")
            return []


# ------------------------------------------------------------------
# Pure-Python math helpers (no numpy required)
# ------------------------------------------------------------------

def _dot(a: List[float], b: List[float]) -> float:
    """Dot product of two equal-length vectors."""
    return sum(x * y for x, y in zip(a, b))


def _magnitude(v: List[float]) -> float:
    """Euclidean magnitude of a vector."""
    return math.sqrt(sum(x * x for x in v))


def _normalise(v: List[float]) -> Optional[List[float]]:
    """Return unit-length vector, or None if magnitude is zero."""
    mag = _magnitude(v)
    if mag == 0.0:
        return None
    return [x / mag for x in v]
