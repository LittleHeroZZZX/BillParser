import importlib
import inspect
import pkgutil
from logging import getLogger

import src.billparser.parsers

from .base import BaseParser

logger = getLogger(__name__)


class ParserManager:
    """
    Manages the discovery, loading, and instantiation of all parsers.

    This class acts as a singleton factory. It is instantiated once
    as 'parser_manager' at the end of this file.
    """

    def __init__(self) -> None:
        self._discovered_classes: dict[str, type[BaseParser]] = (
            self._discover_parser_classes()
        )
        self._parsers = self._load_and_instantiate_parsers()

    def _discover_parser_classes(self) -> dict[str, type[BaseParser]]:
        """
        Walks the 'src.billparser.parsers' package and finds all
        concrete subclasses of BaseParser.
        """

        classes: dict[str, type[BaseParser]] = {}
        package = src.billparser.parsers
        pkg_path = package.__path__
        pkg_name = package.__name__
        for _, module_name, _ in pkgutil.walk_packages(pkg_path, pkg_name + "."):
            try:
                module = importlib.import_module(module_name)
            except Exception as e:
                logger.warning(f"Failed to import module {module_name}: {e}")
                continue

            for _, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, BaseParser)
                    and obj is not BaseParser
                    and not inspect.isabstract(obj)
                ):
                    if obj.name in classes:
                        logger.error(
                            f"Duplicate parser '{obj.name}' found in {module_name}. "
                            f"Already registered in {classes[obj.name].__module__}."
                        )
                        raise ValueError(f"Duplicate parser name: {obj.name}")

                    classes[obj.name] = obj
                    logger.debug(f"Discovered parser class: {obj.name} ({module_name})")
        return classes

    def _load_and_instantiate_parsers(self) -> dict[str, BaseParser]:
        """
        Instantiate parsers registered in yaml settings.
        """
