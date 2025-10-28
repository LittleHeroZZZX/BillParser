import datetime

import pytest

from billparser.models import Bill, RawText, TransactionType
from billparser.parsers.ds_parsers import DeepSeekParser
from billparser.parsers.helpers import asset_helper, bill_helper, category_helper


@pytest.mark.asyncio
async def test_DeepSeekParser():  # noqa: N802
    raw_text_sample = RawText(
        "10:291\nl5G\n90\n账单详情\n北京盒马\n-53.70\n交易成功\n支付时间\n2025-10-26 17:27:53\n付款方式\n招商银行信用卡(1564)>\n商品说明\n盒马工坊双汁白切鸡(姜蓉汁+酱油汁)24\n0g等多件\n支付奖励\n已领取4积分>\n服务详情\n盒马\n盒马\n进入小程序>\nY\n订单号\n202510501m610617070\n商家订单号\nT200P486HC{K11\n账单管理\n账单分类\n餐饮美食\n标签和备注\n添加>\n计入收支\nAAA收款\n回\n联系商家\n申请电子回单\n对此订单有疑问"  # noqa: E501
    )

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
    parser = DeepSeekParser()
    bill = await parser.parse(raw_text_sample)
    bill_helper.compare_bill(bill, expected_bill, raise_on_mismatch=True)
