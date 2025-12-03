from pathlib import Path

import pytest

from billparser.models import RawImage
from billparser.parsers.qianfan_ocr_parser import QianfanOcrParser

test_image_path = Path(__file__).parent / "images" / "alipay" / "1.png"
expected_string_list = [
    "2025-10-26",
    "17:27:53",
    "招商银行信用卡",
    "盒马",
]


@pytest.mark.asyncio
async def test_PPOCRV5Parser():  # noqa: N802
    """Test PPOCRV5Parser with a sample image."""
    with open(test_image_path, "rb") as f:
        file_bytes = f.read()

    ocr_result = await QianfanOcrParser().parse(RawImage(file_bytes))

    for expected_string in expected_string_list:
        assert expected_string in ocr_result, f"Expected '{expected_string}' in OCR result, but got '{ocr_result}'"
