import json
import re
from abc import abstractmethod
from logging import getLogger

from openai import AsyncOpenAI

from ..config import settings
from ..models import Bill, RawText, TransactionType
from .base import BaseParser
from .helpers import PromptHelper, asset_helper, bill_helper, category_helper

logger = getLogger(__name__)


class OpenAICompatibleLLMParser(BaseParser[RawText, Bill]):
    """Base class for any OpenAI-compatible LLM parser."""

    @property
    @abstractmethod
    def client(self) -> AsyncOpenAI:
        pass

    @property
    @abstractmethod
    def model(self) -> str:
        pass

    async def parse(self, input_data: RawText) -> Bill:
        try:
            prompt = PromptHelper.generate_text_to_bill_prompt(input_data)
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You must always end your response with a single valid JSON object and nothing else after it.",  # noqa: E501
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            response_text = response.choices[0].message.content
            if response_text is None:
                raise ValueError(f"Received empty response from {self.name}")
            # Strip <think>...</think> blocks produced by reasoning models (e.g. Qwen3)
            response_text = re.sub(r"<think>.*?</think>", "", response_text, flags=re.DOTALL).strip()
            raw_data = json.loads(response_text)
            transaction_type_str = raw_data.get("transaction_type")
            if transaction_type_str != "信用卡还款":
                catename_str = raw_data.get("catename")
                accountname_str = raw_data.get("accountname")
                assert transaction_type_str in TransactionType, (
                    f"Unknown transaction type '{transaction_type_str}' in {self.name} response"
                )
                assert catename_str in category_helper.categories[transaction_type_str], (
                    f"Unknown category name '{catename_str}' for "
                    f"transaction type '{transaction_type_str}' in {self.name} response"
                )
                assert accountname_str in asset_helper.assets, (
                    f"Unknown account name '{accountname_str}' for "
                    f"transaction type '{transaction_type_str}' in {self.name} response"
                )
                raw_data["transaction_type"] = TransactionType(transaction_type_str)
                raw_data["catename"] = category_helper.get_category(raw_data["transaction_type"], catename_str)
                raw_data["accountname"] = asset_helper.get_asset(accountname_str)
                raw_data["accountname2"] = None
            else:
                raw_data["transaction_type"] = TransactionType.CREDIT_CARD_REPAYMENT
                raw_data["accountname"] = asset_helper.get_asset(raw_data["accountname"])
                raw_data["accountname2"] = asset_helper.get_asset(raw_data["accountname2"])
                raw_data["catename"] = None
            return Bill.model_validate(raw_data)
        except Exception as e:
            logger.error(f"Error during {self.name} parsing: {e}")
            return bill_helper.get_default_bill()


class DeepSeekParser(OpenAICompatibleLLMParser):
    name = "deepseek_chat"

    def __init__(self):
        logger.debug(f"Initializing {self.name}")
        assert self.name in settings["parsers"] or self.name.upper() in settings["parsers"], (
            f"Parser settings for {self.name} not found"
        )
        assert "api_key" in settings["parsers"][self.name] or "API_KEY" in settings["parsers"][self.name], (
            f"API key for {self.name} not found in settings"
        )
        assert "base_url" in settings["parsers"][self.name] or "BASE_URL" in settings["parsers"][self.name], (
            f"Base URL for {self.name} not found in settings"
        )
        assert settings["parsers"][self.name]["api_key"] != "your_deepseek_api_key_here", (
            f"Please set a valid API key for {self.name} in settings.yaml"
        )
        self._client = AsyncOpenAI(
            api_key=settings["parsers"][self.name]["api_key"],
            base_url=settings["parsers"][self.name]["base_url"],
        )

    @property
    def client(self) -> AsyncOpenAI:
        return self._client

    @property
    def model(self) -> str:
        return "deepseek-chat"
