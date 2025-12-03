import base64
import datetime
from logging import getLogger

import httpx

from ..config import settings
from ..models import RawImage, RawText
from .base import BaseParser

logger = getLogger(__name__)


class QianfanOcrParser(BaseParser[RawImage, RawText]):
    name = "Qianfan_OCR"

    def __init__(self):
        logger.debug(f"Initializing {self.name}")
        assert self.name in settings["parsers"] or self.name.upper() in settings["parsers"], (
            f"Parser settings for {self.name} not found"
        )
        self.url = "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic"
        self.api_key = settings["parsers"][self.name]["api_key"]
        self.secret_key = settings["parsers"][self.name]["secret_key"]
        self.access_token = None
        self.access_token_last_updated: datetime.datetime | None = None

        self._update_access_token(force=True)

    def _update_access_token(self, force=True) -> None:
        if self.access_token_last_updated is not None:
            elapsed = datetime.datetime.now() - self.access_token_last_updated
            if elapsed.total_seconds() < 3600 * 24 and not force:
                return
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {"grant_type": "client_credentials", "client_id": self.api_key, "client_secret": self.secret_key}
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        response = httpx.post(url, data=params, headers=headers, timeout=1)
        response.raise_for_status()
        data = response.json()
        self.access_token = data["access_token"]
        self.access_token_last_updated = datetime.datetime.now()

    async def parse(self, input_data: RawImage) -> RawText:
        logger.debug(f"Parsing input data with {self.name}")
        self._update_access_token(force=False)
        data_b64: str = base64.b64encode(input_data).decode("ascii")

        headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
        params = {"access_token": self.access_token}

        pay_load = {
            "image": data_b64,
            "paragraph": "true",
        }
        timeout_config = httpx.Timeout(timeout=10, write=30)

        async with httpx.AsyncClient(timeout=timeout_config) as client:
            response: httpx.Response = await client.post(
                url=self.url,
                data=pay_load,
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            return self._post_process_ocr_response(response.json())

    def _post_process_ocr_response(self, response_json: dict) -> RawText:
        datatext_list = []
        for item in response_json.get("words_result", []):
            datatext_list.append(item["words"])
        paragraph_str_list = []
        for item in response_json.get("paragraphs_result", []):
            idx: list[int] = item["words_result_idx"]
            paragraph_str_list.append("".join([datatext_list[i] for i in idx]))
        detected_text = "\n".join(paragraph_str_list)
        return RawText(detected_text)
