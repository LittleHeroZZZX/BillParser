from pathlib import Path

import pytest

from billparser.models import RawImage
from billparser.parsers.pp_parsers import PPOCRV5Parser

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

    ocr_result = await PPOCRV5Parser().parse(RawImage(file_bytes))
    ocr_text = ocr_result

    for expected_string in expected_string_list:
        assert expected_string in ocr_text
