"""
Azure OpenAI Embeddings — Stage 3.5 of the documentation pipeline.

Embeds each chunk's content using Azure's text-embedding model.
Reuses AZURE_AI_API_KEY from .env (no separate embedding key needed).

Configuration (from .env):
  AZURE_EMBEDDING_ENDPOINT    — e.g. https://your-resource.openai.azure.com/openai/v1
  AZURE_EMBEDDING_DEPLOYMENT  — e.g. text-embedding-ada-002
  AZURE_AI_API_KEY            — same key used for chat completions

Parallelism:
  Batches are submitted concurrently using a ThreadPoolExecutor with
  _EMBED_WORKERS workers (default 4).  Each worker handles one batch
  of up to _BATCH_SIZE texts, so up to 4 × 16 = 64 texts are in-flight
  at the same time.

Graceful degradation: if the API call fails for any reason, the chunk
is left without an embedding and the pipeline continues unaffected.
"""
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional
from runner.config import RunnerConfig


# Batch size — Azure embedding API accepts up to 16 inputs per request
_BATCH_SIZE = 16

# Number of parallel workers that submit embedding batches concurrently
_EMBED_WORKERS = 4


class AzureEmbedder:
    """Compute text embeddings using Azure OpenAI Embeddings API."""

    def __init__(self):
        self.endpoint = (RunnerConfig.AZURE_EMBEDDING_ENDPOINT or "").rstrip("/")
        self.deployment = RunnerConfig.AZURE_EMBEDDING_DEPLOYMENT
        self.api_key = RunnerConfig.AZURE_AI_API_KEY
        self._client = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        """Return True only when all required config is present and non-placeholder."""
        if not self.endpoint or not self.deployment or not self.api_key:
            return False
        lower = self.api_key.lower()
        if any(p in lower for p in ("your-", "placeholder", "here", "xxxx")):
            return False
        return True

    def embed_texts(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Embed a list of text strings in batches.

        Returns a list of float vectors (one per input).
        Failed items are returned as None.
        """
        if not self.is_available():
            raise RuntimeError("Azure Embeddings not configured — check AZURE_EMBEDDING_ENDPOINT, "
                               "AZURE_EMBEDDING_DEPLOYMENT, AZURE_AI_API_KEY in .env")

        client = self._get_client()
        results: List[Optional[List[float]]] = [None] * len(texts)

        # Build batch slices
        batches = [
            (batch_start, texts[batch_start: batch_start + _BATCH_SIZE])
            for batch_start in range(0, len(texts), _BATCH_SIZE)
        ]

        total_batches = len(batches)
        print(f"[Embeddings] Submitting {total_batches} batch(es) across "
              f"{min(_EMBED_WORKERS, total_batches)} parallel worker(s)...")

        # ✅ FAST — parallel workers (up to _EMBED_WORKERS at once)
        with ThreadPoolExecutor(max_workers=_EMBED_WORKERS) as executor:
            futures = {
                executor.submit(self._embed_batch, client, batch): batch_start
                for batch_start, batch in batches
            }
            for future in as_completed(futures):
                batch_start = futures[future]
                batch_size  = len(batches[batch_start // _BATCH_SIZE][1])
                try:
                    batch_vectors = future.result()
                except Exception as e:
                    print(f"[Embeddings] [WARN] Batch @{batch_start} failed: {e}")
                    batch_vectors = [None] * batch_size
                for i, vec in enumerate(batch_vectors):
                    results[batch_start + i] = vec

        return results

    def embed_chunks(self, chunks: List[dict]) -> List[dict]:
        """
        Compute embeddings for each chunk and attach them as chunk["embedding"].

        Mutates chunks in place and returns the same list.
        Chunks whose embedding fails are left unchanged (no "embedding" key).
        """
        if not chunks:
            return chunks

        texts = [self._chunk_text(c) for c in chunks]

        print(f"\n[Embeddings] Computing vectors for {len(chunks)} chunks "
              f"using '{self.deployment}' ({_EMBED_WORKERS} parallel workers)...")

        try:
            vectors = self.embed_texts(texts)
        except Exception as e:
            print(f"[Embeddings] [WARN] Batch embedding failed: {e}")
            return chunks

        embedded = 0
        for chunk, vec in zip(chunks, vectors):
            if vec is not None:
                chunk["embedding"] = vec
                embedded += 1

        print(f"[Embeddings] [OK] {embedded}/{len(chunks)} chunks embedded successfully.")
        return chunks

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_client(self):
        """Lazy-initialize the AzureOpenAI client."""
        if self._client is None:
            # Import here so projects that don't use embeddings don't need openai installed
            from openai import AzureOpenAI
            # The endpoint stored in .env may already include /openai/v1;
            # AzureOpenAI expects the root resource URL.  Strip known suffixes.
            base_endpoint = self.endpoint
            for suffix in ("/openai/v1", "/openai"):
                if base_endpoint.endswith(suffix):
                    base_endpoint = base_endpoint[: -len(suffix)]
                    break

            http_client = None
            if RunnerConfig.SSL_CERT_FILE:
                import httpx
                http_client = httpx.Client(verify=RunnerConfig.SSL_CERT_FILE)

            self._client = AzureOpenAI(
                azure_endpoint=base_endpoint,
                api_key=self.api_key,
                api_version="2024-02-01",   # stable embedding API version
                http_client=http_client,
            )
        return self._client

    def _embed_batch(self, client, texts: List[str]) -> List[Optional[List[float]]]:
        """Call the Azure Embeddings API for one batch with retry."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.embeddings.create(
                    model=self.deployment,
                    input=texts,
                )
                # Sort by index to preserve order
                sorted_data = sorted(response.data, key=lambda d: d.index)
                return [d.embedding for d in sorted_data]
            except Exception as e:
                err = str(e)
                if "429" in err or "rate" in err.lower():
                    delay = 2 ** attempt
                    print(f"[Embeddings] Rate limited — waiting {delay}s (attempt {attempt + 1})")
                    time.sleep(delay)
                    continue
                if attempt == max_retries - 1:
                    print(f"[Embeddings] [WARN] Batch failed after {max_retries} attempts: {e}")
                    return [None] * len(texts)
                time.sleep(1)
        return [None] * len(texts)

    @staticmethod
    def _chunk_text(chunk: dict) -> str:
        """Build a single string to embed from a chunk dict."""
        # Combine category + file paths + first 1000 chars of content for richer signal
        category = chunk.get("category", "")
        paths = " ".join(chunk.get("file_paths", []))
        content = chunk.get("content", "")[:1000]
        return f"[{category}] {paths}\n{content}"


#---------------------Test--------------------#
if __name__ == "__main__":
    embedder = AzureEmbedder()

    print("Available:", embedder.is_available())
    print("Endpoint:", embedder.endpoint)
    print("Deployment:", embedder.deployment)
    print("API Key set:", bool(embedder.api_key))

    if not embedder.is_available():
        print("\n❌ Embeddings not configured — check AZURE_EMBEDDING_ENDPOINT, "
              "AZURE_EMBEDDING_DEPLOYMENT, AZURE_AI_API_KEY in .env")
        raise SystemExit(1)

    # --- Test 1: single-text embedding via embed_texts() ---
    print("\n--- Test 1: embed_texts() with a single string ---")
    try:
        vectors = embedder.embed_texts(["This is a test sentence for embeddings."])
        vec = vectors[0]
        if vec is None:
            print("❌ FAILED: embedding returned None")
        else:
            print(f"✅ SUCCESS: got vector of length {len(vec)}")
            print(f"   First 5 dims: {vec[:5]}")
    except Exception as e:
        print("❌ FAILED:", e)

    # --- Test 2: batch embedding via embed_texts() ---
    print("\n--- Test 2: embed_texts() with multiple strings (batching) ---")
    try:
        sample_texts = [f"Sample document number {i} about API testing." for i in range(3)]
        vectors = embedder.embed_texts(sample_texts)
        ok = all(v is not None for v in vectors)
        lengths = {len(v) for v in vectors if v is not None}
        if ok and len(lengths) == 1:
            print(f"✅ SUCCESS: {len(vectors)}/{len(sample_texts)} embedded, "
                  f"consistent dimensionality = {lengths.pop()}")
        else:
            print(f"⚠️ PARTIAL: {sum(v is not None for v in vectors)}/{len(sample_texts)} "
                  f"embedded successfully; dims seen: {lengths}")
    except Exception as e:
        print("❌ FAILED:", e)

    # --- Test 3: embed_chunks() end-to-end (mutates chunk dicts in place) ---
    print("\n--- Test 3: embed_chunks() ---")
    try:
        test_chunks = [
            {
                "category": "documentation",
                "file_paths": ["docs/readme.md"],
                "content": "This module handles Azure OpenAI embeddings for the pipeline.",
            },
            {
                "category": "code",
                "file_paths": ["runner/config.py"],
                "content": "Runner configuration loaded from environment variables.",
            },
        ]
        embedded_chunks = embedder.embed_chunks(test_chunks)
        for i, c in enumerate(embedded_chunks):
            if "embedding" in c:
                print(f"✅ Chunk {i}: embedding present, length {len(c['embedding'])}")
            else:
                print(f"❌ Chunk {i}: no embedding attached")
    except Exception as e:
        print("❌ FAILED:", e)