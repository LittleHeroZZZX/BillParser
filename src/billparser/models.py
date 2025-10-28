from datetime import datetime
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_serializer, model_validator

RawImage = type("RawImage", (bytes,), {})
RawText = type("RawText", (str,), {})


class TransactionType(StrEnum):
    EXPENSE = "支出"
    INCOME = "收入"
    TRANSFER = "转账"
    CREDIT_CARD_REPAYMENT = "信用卡还款"


class CategoryItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    transaction_type: TransactionType = Field(description="交易类型")
    l1_name: str = Field(description="一级分类名称")
    l1_desc: str = Field(description="一级分类描述")
    l2_name: str | None = Field(description="二级分类名称", default=None)
    l2_desc: str | None = Field(description="二级分类描述", default=None)
    match_rules: list[str] = Field(description="匹配规则列表", default=[])


class AssetItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    account_name: str = Field(description="账户名称")
    account_desc: str = Field(description="账户描述")
    match_rules: list[str] = Field(description="匹配规则列表", default=[])


class Bill(BaseModel):
    model_config = ConfigDict(frozen=True)

    # Refer to https://docs.qianjiapp.com/plugin/auto_tasker.html for details.
    transaction_type: TransactionType = Field(
        description="交易类型，如'支出'、'收入'、'转账'"  # noqa: RUF001
    )
    amount: float = Field(description="交易金额")
    time: datetime = Field(description="交易时间，格式如'2023-10-01 12:34:56'")  # noqa: RUF001
    catename: CategoryItem = Field(description="账单分类")
    remark: str = Field(description="交易备注")
    accountname: AssetItem = Field(description="账单所属账户名称或者转出账户名称")
    accountname2: AssetItem | None = Field(
        default=None, description="转账时的转入账户名称"
    )
    fee: float | None = Field(
        default=None,
        description="手续费",
    )

    @model_validator(mode="after")
    def check_transfer_logic(self) -> Self:
        if self.transaction_type in [
            TransactionType.TRANSFER,
            TransactionType.CREDIT_CARD_REPAYMENT,
        ]:
            if not self.accountname2:
                raise ValueError(
                    "对于转账或者信用卡还款，必须提供 accountname2（转入账户名称）"  # noqa: RUF001
                )
        return self

    @model_validator(mode="after")
    def check_fee_logic(self) -> Self:
        if self.fee is not None and (self.fee < 0 or self.fee > self.amount):
            raise ValueError("手续费 fee 不能为负数且不能大于交易金额 amount")
        return self

    @model_validator(mode="after")
    def check_money_logic(self) -> Self:
        if self.amount <= 0:
            raise ValueError("交易金额 amount 必须为正数")
        return self

    @field_serializer("catename")
    def serialize_catename(self, category: CategoryItem) -> str:
        if category.l2_name:
            return category.l2_name
        return category.l1_name
