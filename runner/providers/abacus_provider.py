"""
Abacus AI Provider — uses Claude Sonnet via the Abacus AI platform.

Configuration (from .env):
  ABACUS_API_KEY — your Abacus AI API key
  ABACUS_DEPLOYMENT_TOKEN — your deployment token
  ABACUS_MODEL — model name (default: claude-sonnet)
"""
import requests
import time
import json
from runner.providers.base import BaseProvider
from runner.config import RunnerConfig


class AbacusProvider(BaseProvider):
    """Abacus AI provider — routes to Claude Sonnet via Abacus AI platform."""

    def __init__(self):
        self.api_key = RunnerConfig.ABACUS_API_KEY
        self.deployment_token = RunnerConfig.ABACUS_DEPLOYMENT_TOKEN
        self.model = RunnerConfig.ABACUS_MODEL
        self.base_url = "https://api.abacus.ai/api/v0"
        self.max_retries = RunnerConfig.MAX_LLM_RETRIES
        self.retry_delay = RunnerConfig.RETRY_BASE_DELAY

     
     
        # Abacus AI is called via plain REST (requests), not an SDK client.
        # `requests` takes `verify=<path-to-cert>` directly on each call —
        # there's no client object to build, so we just remember the path.
        # Falls back to True (use the default CA bundle) if no custom cert is set.
        self.ssl_verify = RunnerConfig.SSL_CERT_FILE or True


    def analyze_chunk(self, system_prompt: str, user_prompt: str) -> str:
        """Send chunk analysis to Abacus AI."""
        return self._call_llm(system_prompt, user_prompt, max_tokens=2000)

    def fill_template(self, system_prompt: str, user_prompt: str) -> str:
        """Send template filling to Abacus AI."""
        return self._call_llm(system_prompt, user_prompt, max_tokens=4000)

    def _call_llm(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> str:
        """Call the Abacus AI LLM API with retry logic."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        payload = {
            "deploymentToken": self.deployment_token,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "maxTokens": max_tokens,
            "temperature": 0.1,
        }

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}/predict",
                    headers=headers,
                    json=payload,
                    timeout=120,
                )

                if response.status_code == 429:
                    # Rate limited — wait and retry
                    retry_after = int(response.headers.get("Retry-After", self.retry_delay * (2 ** attempt)))
                    print(f"[Abacus] Rate limited, waiting {retry_after}s (attempt {attempt + 1})")
                    time.sleep(retry_after)
                    continue

                if response.status_code >= 500:
                    # Server error — retry with backoff
                    delay = self.retry_delay * (2 ** attempt)
                    print(f"[Abacus] Server error {response.status_code}, retrying in {delay}s")
                    time.sleep(delay)
                    continue

                response.raise_for_status()
                data = response.json()

                # Extract text from Abacus AI response
                if isinstance(data, dict):
                    # Try common response formats
                    if "result" in data:
                        return str(data["result"])
                    if "response" in data:
                        return str(data["response"])
                    if "content" in data:
                        return str(data["content"])
                    if "text" in data:
                        return str(data["text"])

                return str(data)

            except requests.exceptions.Timeout:
                delay = self.retry_delay * (2 ** attempt)
                print(f"[Abacus] Timeout, retrying in {delay}s (attempt {attempt + 1})")
                time.sleep(delay)
            except requests.exceptions.ConnectionError:
                delay = self.retry_delay * (2 ** attempt)
                print(f"[Abacus] Connection error, retrying in {delay}s (attempt {attempt + 1})")
                time.sleep(delay)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise RuntimeError(f"Abacus AI call failed after {self.max_retries} attempts: {e}")
                delay = self.retry_delay * (2 ** attempt)
                print(f"[Abacus] Error: {e}, retrying in {delay}s")
                time.sleep(delay)

        raise RuntimeError(f"Abacus AI call failed after {self.max_retries} attempts")

    def get_provider_name(self) -> str:
        return f"Abacus AI ({self.model})"

    def is_available(self) -> bool:
        if not self.api_key or not self.deployment_token:
            return False
        key_lower = str(self.api_key).lower()
        token_lower = str(self.deployment_token).lower()
        if "your-" in key_lower or "placeholder" in key_lower or "here" in key_lower:
            return False
        if "your-" in token_lower or "placeholder" in token_lower or "here" in token_lower:
            return False
        return True


