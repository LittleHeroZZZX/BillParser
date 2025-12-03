import datetime
from pathlib import Path

import pytest

from billparser.models import Bill, TransactionType
from billparser.parsers.helpers import asset_helper, bill_helper, category_helper
from billparser.pipeline import pipeline_manager

test_image_path = Path(__file__).parent / "images" / "alipay" / "1.png"


@pytest.mark.asyncio
async def test_pipeline_manager_initialization():
    """Test that the PipelineManager initializes correctly and loads pipelines."""
    assert pipeline_manager is not None
    assert isinstance(pipeline_manager.pipelines, dict)


@pytest.mark.asyncio
async def test_ocr_then_llm():
    """Test the 'ocr_then_llm' pipeline end-to-end with a sample input."""
    pipeline = pipeline_manager.get_pipeline("ocr_then_llm")
    assert pipeline is not None, "Pipeline 'ocr_then_llm' should be loaded"

    from billparser.models import RawImage

    # Sample image bytes (this should be replaced with actual test image bytes)
    sample_image_bytes = test_image_path.read_bytes()
    input_data = RawImage(sample_image_bytes)
    bill = await pipeline.run(input_data)
    assert isinstance(bill, Bill), "Output should be an instance of Bill"
    expected_bill = Bill(
        transaction_type=TransactionType.EXPENSE,
        amount=53.70,
        time=datetime.datetime(2025, 10, 26, 17, 27, 53),
        catename=category_helper.get_category(TransactionType.EXPENSE, "外卖"),
        remark="盒马工坊双汁白切鸡(姜蓉汁+酱油汁)240g等多件",
        accountname=asset_helper.get_asset("招商银行信用卡"),
        accountname2=None,
        fee=None,
    )
    bill_helper.compare_bill(bill, expected_bill, raise_on_mismatch=True, skip_remark=True)
