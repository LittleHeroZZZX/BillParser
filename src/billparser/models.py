from datetime import datetime
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

RawImage = type("RawImage", (bytes,), {})
RawText = type("RawText", (str,), {})


class TransactionType(StrEnum):
    EXPENSE = "支出"
    INCOME = "收入"
    TRANSFER = "转账"
    CREDIT_CARD_REPAYMENT = "信用卡还款"


class Bill(BaseModel):
    model_config = ConfigDict(frozen=True)

    # See https://docs.qianjiapp.com/plugin/auto_tasker.html for details
    transaction_type: TransactionType = Field(
        description="交易类型，如'支出'、'收入'、'转账'"  # noqa: RUF001
    )
    amount: float = Field(description="交易金额")
    time: datetime = Field(description="交易时间，格式如'2023-10-01 12:34:56'")  # noqa: RUF001
    remark: str = Field(description="交易备注")
    accountname: str = Field(description="账单所属账户名称或者转出账户名称")
    accountname2: str | None = Field(default=None, description="转账时的转入账户名称")
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
        if self.fee is not None and self.fee < self.amount:
            raise ValueError("手续费 fee 不能为负数且不能大于交易金额 amount")
        return self

    @model_validator(mode="after")
    def check_money_logic(self) -> Self:
        if self.amount <= 0:
            raise ValueError("交易金额 amount 必须为正数")
        return self
