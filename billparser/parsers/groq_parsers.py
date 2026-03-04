from logging import getLogger

from openai import AsyncOpenAI

from ..config import settings
from .ds_parsers import OpenAICompatibleLLMParser

logger = getLogger(__name__)

GROQ_BASE_URL = "https://api.groq.com/openai/v1"


class GroqParser(OpenAICompatibleLLMParser):
    name = "groq"

    def __init__(self):
        logger.debug(f"Initializing {self.name}")
        assert self.name in settings["parsers"] or self.name.upper() in settings["parsers"], (
            f"Parser settings for {self.name} not found"
        )
        parser_cfg = settings["parsers"][self.name]
        assert "api_key" in parser_cfg, f"api_key for {self.name} not found in settings"
        assert "model" in parser_cfg, f"model for {self.name} not found in settings"
        self._client = AsyncOpenAI(
            api_key=parser_cfg["api_key"],
            base_url=GROQ_BASE_URL,
        )
        self._model = parser_cfg["model"]

    @property
    def client(self) -> AsyncOpenAI:
        return self._client

    @property
    def model(self) -> str:
        return self._model
