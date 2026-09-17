from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    def generate_structured(self, system_prompt: str, user_text: str) -> dict:
        """
        Generates a structured JSON dict from the LLM based on the text.
        Returns the parsed dictionary.
        """
        pass
