import base64
from abc import abstractmethod
from logging import getLogger

import httpx

from ..config import settings
from ..models import RawImage, RawText
from .base import BaseParser

logger = getLogger(__name__)


class PpParserBase(BaseParser[RawImage, RawText]):
    def __init__(self):
        logger.debug(f"Initializing {self.name}")
        assert self.name in settings["parsers"] or self.name.upper() in settings["parsers"], (
            f"Parser settings for {self.name} not found"
        )
        self.url = settings["parsers"][self.name]["url"]
        self.token = settings["parsers"][self.name]["token"]

    async def parse(self, input_data: RawImage) -> RawText:
        logger.debug(f"Parsing input data with {self.name}")
        data_b64: str = base64.b64encode(input_data).decode("ascii")

        headers = {
            "Authorization": f"token {self.token}",
            "Content-Type": "application/json",
        }

        pay_load = {
            "file": data_b64,
            "fileType": 1,  # 1 for image, 0 for PDF
        }
        timeout_config = httpx.Timeout(timeout=10, write=30)

        async with httpx.AsyncClient(timeout=timeout_config) as client:
            response: httpx.Response = await client.post(
                url=self.url,
                json=pay_load,
                headers=headers,
            )
            response.raise_for_status()
            return self._post_process_ocr_response(response.json())

    @abstractmethod
    def _post_process_ocr_response(self, response_json: dict) -> RawText:
        pass


class PPOCRV5Parser(PpParserBase):
    name = "PP_OCRv5"

    def _post_process_ocr_response(self, response_json: dict) -> RawText:
        datatext_list = response_json["result"]["ocrResults"][0]["prunedResult"]["rec_texts"]
        detected_text = "\n".join(datatext_list)
        return RawText(detected_text)
