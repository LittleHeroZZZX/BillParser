# src/billparser/parsers/base.py
from abc import ABC, abstractmethod
from typing import TypeVar

from src.billparser.models import Bill, RawImage, RawText

T_Input = TypeVar("T_Input", bound=RawImage | RawText)
T_Output = TypeVar("T_Output", bound=Bill | RawText)


class BaseParser[T_Input, T_Output](ABC):
    """
    Generic Parser interface for bill parsing.
    """

    name: str  # Unique name of the parser

    @abstractmethod
    def __init__(self):
        pass

    @property
    def input_type(self) -> type[T_Input]:
        """
        Input data type that this parser accepts.
        (Automatically derived from the Generic[T_Input, ...])
        """
        return self.__orig_bases__[0].__args__[0]  # type: ignore[attr-defined]

    @property
    def output_type(self) -> type[T_Output]:
        """
        Output data type that this parser produces.
        (Automatically derived from the Generic[..., T_Output])
        """
        return self.__orig_bases__[0].__args__[1]  # type: ignore[attr-defined]

    @abstractmethod
    async def parse(self, input_data: T_Input) -> T_Output:
        """
        Parse the input data and return the output data.
        """
        pass
