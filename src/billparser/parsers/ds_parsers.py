import json
from logging import getLogger

from openai import AsyncOpenAI

from ..config import settings
from ..models import TransactionType
from .base import BaseParser, Bill, RawText
from .helpers import PromptHelper, asset_helper, bill_helper, category_helper

logger = getLogger(__name__)


class DeepSeekParser(BaseParser[RawText, Bill]):
    name = "deepseek_chat"

    def __init__(self):
        logger.debug(f"Initializing {self.name}")
        assert self.name in settings["parsers"], (
            f"Parser settings for {self.name} not found"
        )
        assert "api_key" in settings["parsers"][self.name], (
            f"API key for {self.name} not found in settings"
        )
        assert "base_url" in settings["parsers"][self.name], (
            f"Base URL for {self.name} not found in settings"
        )
        assert (
            settings["parsers"][self.name]["api_key"] != "your_deepseek_api_key_here"
        ), f"Please set a valid API key for {self.name} in settings.yaml"
        self.client = AsyncOpenAI(
            api_key=settings["parsers"][self.name]["api_key"],
            base_url=settings["parsers"][self.name]["base_url"],
        )

    async def parse(self, input_data: RawText) -> Bill:
        try:
            prompt = PromptHelper.generate_text_to_bill_prompt(input_data)
            response = await self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
            )
            response_text = response.choices[0].message.content
            if response_text is None:
                raise ValueError("Received empty response from DeepSeek API")
            raw_data = json.loads(response_text)
            transaction_type_str = raw_data.get("transaction_type")
            catename_str = raw_data.get("catename")
            accountname_str = raw_data.get("accountname")
            assert transaction_type_str in TransactionType, (
                f"Unknown transaction type '{transaction_type_str}' "
                "in DeepSeek response"
            )
            assert catename_str in category_helper.categories[transaction_type_str], (
                f"Unknown category name '{catename_str}' for "
                f"transaction type '{transaction_type_str}' in DeepSeek response"
            )
            assert accountname_str in asset_helper.assets, (
                f"Unknown account name '{accountname_str}' for "
                f"transaction type '{transaction_type_str}' in DeepSeek response"
            )
            raw_data["transaction_type"] = TransactionType(transaction_type_str)
            raw_data["catename"] = category_helper.get_category(
                raw_data["transaction_type"], catename_str
            )
            raw_data["accountname"] = asset_helper.get_asset(accountname_str)
            return Bill.model_validate(raw_data)
        except Exception as e:
            logger.error(f"Error during DeepSeek parsing: {e}")
            return bill_helper.get_default_bill()
