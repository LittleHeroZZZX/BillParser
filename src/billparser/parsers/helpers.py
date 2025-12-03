from datetime import datetime
from logging import getLogger

from ..config import settings
from ..models import AssetItem, Bill, CategoryItem, RawText, TransactionType

logger = getLogger(__name__)


class CategoryHelper:
    """
    A helper class for category-related operations, including:
        - Loading category mappings from settings.
        - Getting category by transaction type and name.
        - Dumping categories to text prompt format.
    """

    def __init__(self) -> None:
        self._initialized = False

    def _initialize(self):
        if self._initialized:
            return
        assert "categories" in settings, "Category settings not found"
        self.categories: dict[TransactionType, dict[str, CategoryItem]] = {}
        for category_group in settings["categories"]:
            transaction_type_str = category_group.get("transaction_type")
            if not transaction_type_str:
                logger.warning("Transaction type missing in category settings")
                continue
            if transaction_type_str not in TransactionType:
                logger.warning(f"Unknown transaction type '{transaction_type_str}' in category settings")
                continue
            transaction_type_enum = TransactionType(transaction_type_str)
            self.categories[transaction_type_enum] = {}
            l1_items = category_group.get("items", [])
            for l1_item in l1_items:
                l1_name = l1_item["l1_name"]
                l1_desc = l1_item.get("description", "")
                l2_items = l1_item.get("items", [])
                if len(l2_items) == 0:
                    category_item = CategoryItem(
                        transaction_type=transaction_type_enum,
                        l1_name=l1_name,
                        l1_desc=l1_desc,
                        l2_name=None,
                        l2_desc=None,
                        match_rules=l1_item.get("match_rules", []),
                    )
                    self.categories[transaction_type_enum][l1_name] = category_item
                else:
                    for l2_item in l2_items:
                        l2_name = l2_item["l2_name"]
                        l2_desc = l2_item.get("description", "")
                        category_item = CategoryItem(
                            transaction_type=transaction_type_enum,
                            l1_name=l1_name,
                            l1_desc=l1_desc,
                            l2_name=l2_name,
                            l2_desc=l2_desc,
                            match_rules=l2_item.get("match_rules", []),
                        )
                        self.categories[transaction_type_enum][l2_name] = category_item
        self._initialized = True

    def get_category(self, transaction_type: TransactionType, name: str) -> CategoryItem:
        """
        Get category item by transaction type and name.

        """
        self._initialize()
        if transaction_type not in self.categories:
            logger.warning(f"Transaction type '{transaction_type}' not found in categories")
            return self.get_default_category()
        if name not in self.categories[transaction_type]:
            logger.warning(f"Category name '{name}' not found under transaction type '{transaction_type}'")
            return self.get_default_category()
        return self.categories[transaction_type].get(name, self.get_default_category())

    def dump_categories_to_prompt(self) -> str:
        """
        Dump categories to text prompt format.

        Returns:
            str: Categories in text prompt format.
        """
        self._initialize()
        prompt_lines = []
        for transaction_type, categories in self.categories.items():
            for category in categories.values():
                if category.l2_name:
                    line = (
                        f"- 交易类型: {transaction_type.value}, "
                        f"一级分类: {category.l1_name}, "
                        f"一级分类描述: {category.l1_desc}, "
                        f"二级分类: {category.l2_name}, "
                        f"二级分类描述: {category.l2_desc}, "
                        f"强制匹配规则: {category.match_rules}"
                    )
                else:
                    line = (
                        f"- 交易类型: {transaction_type.value}, "
                        f"一级分类: {category.l1_name}, "
                        f"一级分类描述: {category.l1_desc}, "
                        f"二级分类: {category.l1_name}, "
                        f"二级分类描述: {category.l1_desc}, "
                        f"强制匹配规则: {category.match_rules}"
                    )
                prompt_lines.append(line)
        return "\n".join(prompt_lines)

    def get_default_category(self) -> CategoryItem:
        """
        Get default category item for a given transaction type.
        """
        return CategoryItem(
            transaction_type=TransactionType.EXPENSE,
            l1_name="其它",
            l1_desc="其它",
            l2_name="其它",
            l2_desc="其它",
            match_rules=[],
        )


class AssetHelper:
    """
    A helper class for asset-related operations, including:
        - Loading asset mappings from settings.
        - Getting asset by account name.
        - Dumping assets to text prompt format.
    """

    def __init__(self) -> None:
        self._initialized = False

    def _initialize(self):
        if self._initialized:
            return
        assert "assets" in settings, "Asset settings not found"
        self.assets: dict[str, AssetItem] = {}
        asset_items = settings.get("assets", [])
        for asset_item in asset_items:
            account_name = asset_item["account_name"]
            account_desc = asset_item.get("description", "")
            match_rules = asset_item.get("match_rules", [])
            asset = AssetItem(
                account_name=account_name,
                account_desc=account_desc,
                match_rules=match_rules,
            )
            self.assets[account_name] = asset

    def get_asset(self, account_name: str) -> AssetItem:
        """
        Get asset item by account name.

        """
        self._initialize()
        if account_name not in self.assets:
            logger.warning(f"Account name '{account_name}' not found in assets")
            return self.get_default_asset()
        return self.assets.get(account_name, self.get_default_asset())

    def dump_assets_to_prompt(self) -> str:
        """
        Dump assets to text prompt format.

        Returns:
            str: Assets in text prompt format.
        """
        self._initialize()
        prompt_lines = []
        for asset in self.assets.values():
            line = (
                f"- 账户名称: {asset.account_name}, 账户描述: {asset.account_desc}, 强制匹配规则: {asset.match_rules}"
            )
            prompt_lines.append(line)
        return "\n".join(prompt_lines)

    def get_default_asset(self) -> AssetItem:
        """
        Get default asset item.
        """
        return AssetItem(
            account_name="无",
            account_desc="无",
            match_rules=[],
        )


class PromptHelper:
    """
    A helper class for generating prompts using category and asset helpers.
    """

    @classmethod
    def generate_text_to_bill_prompt(cls, raw_text: RawText) -> str:
        category_prompt = category_helper.dump_categories_to_prompt()
        asset_prompt = asset_helper.dump_assets_to_prompt()

        prompt = f"""
You are an expert accounting assistant.
Analyze the provided bill text and extract the fields into a valid JSON object.
You must only return a single, minified JSON object and nothing else.
The JSON must conform to this Pydantic schema:
{{
            "transaction_type": "'支出' | '收入' | '转账' | '信用卡还款'",
    "amount": "float",
    "time": "string" (format: 'YYYY-MM-DD HH:MM:SS'),
    "catename": "string" (See rules below),
    "remark": "string|null", (See rules below)
    "accountname": "string" (The merchant or person),
    "accountname2": "string|null" (See rules below),
    "fee": "float | null"
}}

Here are the detailed rules:
- transaction_type
    交易类型。值必须是 '支出', '收入', '转账', 或 '信用卡还款' 之一。
    转账指的是在自己资产之间资金的流动。
- amount
    交易金额。必须是一个正数，表示交易的金额。
- time
    交易时间。必须是一个字符串，格式为 'YYYY-MM-DD HH:MM:SS'。
- catename
    交易类别。必须从后文给出的交易类别中选择一个最符合的类别，值为其中二级分类名(l2_name)，并且交易类型与该分类名的交易类型严格一致。
- remark
    交易备注。必须是一个字符串，通常为 null，对于大额交易，可以考虑备注购买的商品。
- accountname
    账户名称。必须从后文给出的资产列表中选择一个最符合的账户名称，值为其中的账户名称(account_name)。
    对于任意交易类型，该字段均不能为空，表示交易中资金的流出方。
- accountname2
    账户名称2。当且仅当 transaction_type 为 '转账' 或 '信用卡还款' 时，该字段必须是一个非空字符串，表示资金的流入方。
- fee
    交易手续费。可以是一个浮点数或 null，表示交易的手续费，绝大多数情况为 null。

以下为交易类别列表:
{category_prompt}

以下为资产列表:
{asset_prompt}

请根据账单截图的 OCR 文字内容，提取并返回符合上述 Pydantic 模式的 JSON 对象。

以下为 OCR 文字内容:
{raw_text}

账单内容到此结束

再次强调，你的回复必须仅包含一个符合上述 Pydantic 模式的 JSON 对象，且不能包含任何其他文本。
如果没有识别到有效信息，请将amount字段设为-1，并将其他字段设为null或合适的空值。
"""  # noqa: RUF001

        return prompt.strip()


class BillHelper:
    @classmethod
    def get_default_bill(cls) -> Bill:
        return Bill(
            transaction_type=TransactionType.EXPENSE,
            amount=0.1,
            time=datetime.now(),
            catename=category_helper.get_default_category(),
            remark="",
            accountname=asset_helper.get_default_asset(),
            accountname2=None,
            fee=None,
        )

    @classmethod
    def compare_bill(
        cls,
        bill1: Bill,
        bill2: Bill,
        *,
        skip_transaction_type=False,
        skip_amount=False,
        skip_time=False,
        skip_catename=False,
        skip_remark=False,
        skip_accountname=False,
        skip_accountname2=False,
        skip_fee=False,
        raise_on_mismatch=False,
    ) -> bool:
        """
        Compare two Bill objects with options to skip certain fields.

        Returns:
            bool: True if bills are equal (considering skipped fields), False otherwise.
        """
        try:
            if not skip_transaction_type and bill1.transaction_type != bill2.transaction_type:
                raise ValueError(
                    f"transaction_type mismatch, bill1: {bill1.transaction_type}, bill2: {bill2.transaction_type}"
                )
            if not skip_amount and bill1.amount != bill2.amount:
                raise ValueError(f"amount mismatch, bill1: {bill1.amount}, bill2: {bill2.amount}")
            if not skip_time and bill1.time != bill2.time:
                raise ValueError(f"time mismatch, bill1: {bill1.time}, bill2: {bill2.time}")
            if not skip_catename and bill1.catename != bill2.catename:
                raise ValueError(f"catename mismatch, bill1: {bill1.catename}, bill2: {bill2.catename}")
            if not skip_remark and bill1.remark != bill2.remark:
                raise ValueError(f"remark mismatch, bill1: {bill1.remark}, bill2: {bill2.remark}")
            if not skip_accountname and bill1.accountname != bill2.accountname:
                raise ValueError(f"accountname mismatch, bill1: {bill1.accountname}, bill2: {bill2.accountname}")
            if not skip_accountname2 and bill1.accountname2 != bill2.accountname2:
                raise ValueError(f"accountname2 mismatch, bill1: {bill1.accountname2}, bill2: {bill2.accountname2}")
            if not skip_fee and bill1.fee != bill2.fee:
                raise ValueError(f"fee mismatch, bill1: {bill1.fee}, bill2: {bill2.fee}")
            return True
        except ValueError as e:
            if raise_on_mismatch:
                raise
            logger.debug(f"Bill comparison failed: {e}")
            return False


category_helper = CategoryHelper()
asset_helper = AssetHelper()
bill_helper = BillHelper()
