# src/billparser/parsers/base.py
from abc import ABC, abstractmethod
from typing import TypeVar, get_args, get_origin

from ..models import ParserInput, ParserOutput

T_Input = TypeVar("T_Input", bound=ParserInput)
T_Output = TypeVar("T_Output", bound=ParserOutput)


class BaseParser[T_Input, T_Output](ABC):
    """
    Generic Parser interface for bill parsing.
    """

    name: str  # Unique name of the parser

    @abstractmethod
    def __init__(self):
        pass

    @classmethod
    def _get_parser_generic_args(cls) -> tuple[type, type]:
        """
        Retrieve the concrete types used for T_Input and T_Output.
        """
        if hasattr(cls, "_cached_base_args"):
            return cls._cached_base_args
        orig_bases = getattr(cls, "__orig_bases__", ())
        for base in orig_bases:
            origin = get_origin(base)
            if origin is BaseParser:
                args = get_args(base)
                cls._cached_base_args = args
                return args
        raise TypeError("Could not determine generic arguments for BaseParser")

    @property
    def input_type(self) -> type[T_Input]:
        """
        Input data type that this parser accepts.
        (Automatically derived from the Generic[T_Input, ...])
        """
        return self._get_parser_generic_args()[0]

    @property
    def output_type(self) -> type[T_Output]:
        """
        Output data type that this parser produces.
        (Automatically derived from the Generic[..., T_Output])
        """
        return self._get_parser_generic_args()[1]

    @abstractmethod
    async def parse(self, input_data: T_Input) -> T_Output:
        """
        Parse the input data and return the output data.
        """
        pass

    def __repr__(self) -> str:
        return (
            f"<Parser name={self.name} input_type={self.input_type.__name__} output_type={self.output_type.__name__}>"
        )
