"""
Azure AI Foundry Provider — supports any model deployed on Azure AI Foundry.

Configuration (from .env):
  AZURE_AI_ENDPOINT — your Azure AI resource endpoint
  AZURE_AI_API_KEY — your Azure AI API key
  AZURE_AI_DEPLOYMENT_NAME — your model deployment name
  AZURE_AI_API_VERSION — API version (default: 2024-06-01)
"""
import time
from openai import AzureOpenAI
from runner.providers.base import BaseProvider
from runner.config import RunnerConfig


class AzureAIProvider(BaseProvider):
    """Azure AI Foundry provider — supports any deployed model."""

    def __init__(self):
        self.endpoint = RunnerConfig.AZURE_AI_ENDPOINT
        self.api_key = RunnerConfig.AZURE_AI_API_KEY
        self.deployment_name = RunnerConfig.AZURE_AI_DEPLOYMENT_NAME
        self.api_version = RunnerConfig.AZURE_AI_API_VERSION
        self.max_retries = RunnerConfig.MAX_LLM_RETRIES
        self.retry_delay = RunnerConfig.RETRY_BASE_DELAY

        if self.is_available():
            self.client = AzureOpenAI(
                azure_endpoint=self.endpoint,
                api_key=self.api_key,
                api_version=self.api_version,
            )
        else:
            self.client = None

    def analyze_chunk(self, system_prompt: str, user_prompt: str) -> str:
        """Send chunk analysis to Azure AI."""
        return self._call_llm(system_prompt, user_prompt, max_tokens=2000)

    def fill_template(self, system_prompt: str, user_prompt: str) -> str:
        """Send template filling to Azure AI."""
        return self._call_llm(system_prompt, user_prompt, max_tokens=4000)

    def _call_llm(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> str:
        """Call Azure AI with retry logic, handling both max_completion_tokens and max_tokens."""
        if not self.client:
            raise RuntimeError("Azure AI Foundry is not configured. Check AZURE_AI_* env vars.")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        for attempt in range(self.max_retries):
            try:
                # Try max_completion_tokens first (required for modern models like gpt-4o, gpt-5.x, o1, etc.)
                try:
                    response = self.client.chat.completions.create(
                        model=self.deployment_name,
                        messages=messages,
                        max_completion_tokens=max_tokens,
                        temperature=0.1,
                    )
                except Exception as param_err:
                    err_lower = str(param_err).lower()
                    if "max_tokens" in err_lower or "unsupported_parameter" in err_lower:
                        # Fallback to max_tokens for legacy models
                        response = self.client.chat.completions.create(
                            model=self.deployment_name,
                            messages=messages,
                            max_tokens=max_tokens,
                            temperature=0.1,
                        )
                    else:
                        raise param_err

                if response.choices and response.choices[0].message:
                    return response.choices[0].message.content or ""

                return ""

            except Exception as e:
                error_str = str(e)

                # Rate limiting
                if "429" in error_str or "rate" in error_str.lower():
                    delay = self.retry_delay * (2 ** attempt)
                    print(f"[Azure AI] Rate limited, waiting {delay}s (attempt {attempt + 1})")
                    time.sleep(delay)
                    continue

                # Server errors
                if any(code in error_str for code in ["500", "502", "503", "504"]):
                    delay = self.retry_delay * (2 ** attempt)
                    print(f"[Azure AI] Server error, retrying in {delay}s (attempt {attempt + 1})")
                    time.sleep(delay)
                    continue

                # Last attempt — raise
                if attempt == self.max_retries - 1:
                    raise RuntimeError(f"Azure AI call failed after {self.max_retries} attempts: {e}")

                delay = self.retry_delay * (2 ** attempt)
                print(f"[Azure AI] Error: {e}, retrying in {delay}s")
                time.sleep(delay)

        raise RuntimeError(f"Azure AI call failed after {self.max_retries} attempts")

    def get_provider_name(self) -> str:
        return f"Azure AI Foundry ({self.deployment_name})"

    def is_available(self) -> bool:
        if not self.endpoint or not self.api_key or not self.deployment_name:
            return False
        key_lower = str(self.api_key).lower()
        if "your-" in key_lower or "placeholder" in key_lower or "here" in key_lower:
            return False
        return True
