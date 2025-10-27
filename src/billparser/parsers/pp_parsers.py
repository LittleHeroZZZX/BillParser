import base64
from abc import abstractmethod
from logging import getLogger

import httpx

from ..config import settings
from ..models import RawImage, RawText
from .base import BaseParser

logger = getLogger(__name__)


class PpParserBase(BaseParser):
    def __init__(self):
        logger.debug(f"Initializing {self.name}")
        assert self.name in settings["parsers"]
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

        async with httpx.AsyncClient() as client:
            response: httpx.Response = await client.post(
                url=self.url,
                json=pay_load,
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            return self._post_process_ocr_response(response.json())

    @abstractmethod
    def _post_process_ocr_response(self, response_json: dict) -> RawText:
        pass


class PPOCRV5Parser(PpParserBase):
    name = "PP-OCRv5"

    def _post_process_ocr_response(self, response_json: dict) -> RawText:
        datatext_list = response_json["result"]["ocrResults"][0]["prunedResult"][
            "rec_texts"
        ]
        detected_text = "\n".join(datatext_list)
        return RawText(detected_text)
