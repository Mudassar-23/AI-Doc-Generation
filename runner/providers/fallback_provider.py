"""
Fallback AI Provider — wraps Abacus, Azure AI, and Mock AI providers.
If the preferred provider fails during a request, it falls back to the next available provider.
"""
from typing import Optional
from runner.providers.base import BaseProvider
from runner.providers.abacus_provider import AbacusProvider
from runner.providers.azure_ai_provider import AzureAIProvider
from runner.providers.mock_provider import MockProvider


class FallbackProvider(BaseProvider):
    """Resilient provider that tries Abacus, falls back to Azure AI, and then to Mock."""

    def __init__(self, preferred_provider_name: str = "abacus"):
        self.preferred_name = preferred_provider_name
        self.abacus = AbacusProvider()
        self.azure = AzureAIProvider()
        self.mock = MockProvider()

    def analyze_chunk(self, system_prompt: str, user_prompt: str) -> str:
        """Send chunk analysis to the first working provider in sequence."""
        providers = self._get_provider_sequence()
        errors = []

        for provider, name in providers:
            if provider.is_available() or name == "Mock Provider":
                try:
                    print(f"[FallbackProvider] Trying {name} for chunk analysis...")
                    return provider.analyze_chunk(system_prompt, user_prompt)
                except Exception as e:
                    err_msg = f"{name} failed chunk analysis: {e}"
                    print(f"[FallbackProvider] WARNING: {err_msg}")
                    errors.append(err_msg)
            else:
                print(f"[FallbackProvider] Skipping {name} (not configured/available).")

        # Fallback to mock as absolute safety
        print("[FallbackProvider] Critical: All LLM providers failed. Falling back to Mock Provider.")
        return self.mock.analyze_chunk(system_prompt, user_prompt)

    def fill_template(self, system_prompt: str, user_prompt: str) -> str:
        """Send template filling to the first working provider in sequence."""
        providers = self._get_provider_sequence()
        errors = []

        for provider, name in providers:
            if provider.is_available() or name == "Mock Provider":
                try:
                    print(f"[FallbackProvider] Trying {name} for template filling...")
                    return provider.fill_template(system_prompt, user_prompt)
                except Exception as e:
                    err_msg = f"{name} failed template filling: {e}"
                    print(f"[FallbackProvider] WARNING: {err_msg}")
                    errors.append(err_msg)
            else:
                print(f"[FallbackProvider] Skipping {name} (not configured/available).")

        # Fallback to mock as absolute safety
        print("[FallbackProvider] Critical: All LLM providers failed. Falling back to Mock Provider.")
        return self.mock.fill_template(system_prompt, user_prompt)

    def get_provider_name(self) -> str:
        """Return the provider description."""
        return f"Fallback Provider (Preferred: {self.preferred_name})"

    def is_available(self) -> bool:
        """FallbackProvider is always available."""
        return True

    def _get_provider_sequence(self):
        """Build sequence of providers to try based on preferred configuration and availability."""
        if self.preferred_name == "azure_ai":
            return [
                (self.azure, "Azure AI"),
                (self.abacus, "Abacus AI"),
                (self.mock, "Mock Provider")
            ]
        elif self.preferred_name == "abacus":
            return [
                (self.abacus, "Abacus AI"),
                (self.azure, "Azure AI"),
                (self.mock, "Mock Provider")
            ]
        else:
            # Automatic detection: try available real APIs first before mock
            sequence = []
            if self.abacus.is_available():
                sequence.append((self.abacus, "Abacus AI"))
            if self.azure.is_available():
                sequence.append((self.azure, "Azure AI"))
            sequence.append((self.mock, "Mock Provider"))
            return sequence
