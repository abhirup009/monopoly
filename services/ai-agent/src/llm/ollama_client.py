"""Ollama LLM client wrapper."""

import logging
from typing import Any

from ollama import AsyncClient

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for local Ollama LLM."""

    def __init__(
        self,
        model: str = "llama3",
        host: str = "http://localhost:11434",
    ):
        """Initialize the Ollama client.

        Args:
            model: Model name to use (e.g., "llama3", "llama3:8b")
            host: Ollama server URL
        """
        self.model = model
        self.host = host
        self.client = AsyncClient(host=host)

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        context: list[int] | None = None,
    ) -> tuple[str, list[int]]:
        """Generate a response from the LLM.

        Args:
            system_prompt: System/personality prompt
            user_prompt: User message (game state and question)
            temperature: Randomness (0.0-1.0)
            context: Previous conversation context for continuity

        Returns:
            Tuple of (response_text, new_context)
        """
        try:
            response = await self.client.generate(
                model=self.model,
                system=system_prompt,
                prompt=user_prompt,
                context=context,
                options={
                    "temperature": temperature,
                    "num_predict": 300,  # Limit response length
                    "top_p": 0.9,
                },
            )

            response_text = response.get("response", "")
            new_context = response.get("context", [])

            logger.debug(f"LLM response: {response_text[:200]}...")

            return response_text, new_context

        except Exception as e:
            logger.error(f"Ollama generate error: {e}")
            raise

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
    ) -> str:
        """Chat-style generation with message history.

        Args:
            messages: List of {"role": "system"|"user"|"assistant", "content": "..."}
            temperature: Randomness (0.0-1.0)

        Returns:
            Assistant response text
        """
        try:
            response = await self.client.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": 300,
                },
            )

            return response.get("message", {}).get("content", "")

        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            raise

    async def is_available(self) -> bool:
        """Check if Ollama is running and model is available.

        Returns:
            True if Ollama is available and model is loaded
        """
        try:
            models = await self.client.list()
            model_names = [m.get("name", "") for m in models.get("models", [])]

            # Check if our model is available (handle tags like llama3:8b)
            base_model = self.model.split(":")[0]
            available = any(
                name.startswith(base_model) or name.startswith(self.model)
                for name in model_names
            )

            if not available:
                logger.warning(
                    f"Model {self.model} not found. Available: {model_names}"
                )

            return available

        except Exception as e:
            logger.error(f"Ollama availability check failed: {e}")
            return False

    async def get_model_info(self) -> dict[str, Any] | None:
        """Get information about the loaded model.

        Returns:
            Model info dict or None if not available
        """
        try:
            return await self.client.show(self.model)
        except Exception:
            return None
