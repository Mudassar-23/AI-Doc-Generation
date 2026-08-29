"""
Abstract base class for AI providers.
All providers (Abacus AI, Azure AI Foundry, Mock) implement this interface.
"""
from abc import ABC, abstractmethod
from typing import Optional


class BaseProvider(ABC):
    """Abstract AI provider interface."""

    @abstractmethod
    def analyze_chunk(self, system_prompt: str, user_prompt: str) -> str:
        """
        Send a chunk analysis prompt to the LLM.

        Args:
            system_prompt: The system prompt for chunk analysis.
            user_prompt: The user prompt containing the chunk content.

        Returns:
            The LLM's response as a string (expected to be valid JSON).
        """
        pass

    @abstractmethod
    def fill_template(self, system_prompt: str, user_prompt: str) -> str:
        """
        Send a template filling prompt to the LLM.

        Args:
            system_prompt: The system prompt for template filling.
            user_prompt: The user prompt containing template + context.

        Returns:
            The LLM's response as a string (completed Markdown).
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider name for logging."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is properly configured and available."""
        pass
