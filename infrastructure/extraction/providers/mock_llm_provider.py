from packages.domain.extraction.llm_provider import LLMProvider


class MockLLMProvider(LLMProvider):
    def __init__(self):
        self.mock_response = {}

    def set_mock_response(self, response: dict):
        self.mock_response = response

    def generate_structured(self, system_prompt: str, user_text: str) -> dict:
        return self.mock_response
