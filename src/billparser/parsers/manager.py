import importlib
import inspect
import pkgutil
import sys
from logging import getLogger

from ..config import settings
from .base import BaseParser

logger = getLogger(__name__)


class ParserManager:
    """
    Manages the discovery, loading, and instantiation of all parsers.

    This class acts as a singleton factory. It is instantiated once
    as 'parser_manager' at the end of this file.
    """

    def __init__(self) -> None:
        self._discovered_classes: dict[str, type[BaseParser]] = self._discover_parser_classes()
        self._registry = self._load_and_instantiate_parsers()

    def _discover_parser_classes(self) -> dict[str, type[BaseParser]]:
        """
        Walks the 'src.billparser.parsers' package and finds all
        concrete subclasses of BaseParser.
        """
        classes: dict[str, type[BaseParser]] = {}
        package = sys.modules[__name__.rpartition(".")[0]]
        pkg_path = package.__path__
        pkg_name = package.__name__
        for _, module_name, _ in pkgutil.walk_packages(pkg_path, pkg_name + "."):
            if module_name.endswith(("manager", "base", "helpers")):
                continue
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
                    if not hasattr(obj, "name"):
                        logger.warning(
                            f"Parser class {obj.__name__} in {module_name} does not have a 'name' attribute."
                        )
                        continue
                    name = obj.name.lower()
                    if name in classes:
                        logger.error(
                            f"Duplicate parser '{name}' found in {module_name}. "
                            f"Already registered in {classes[name].__module__}."
                        )
                        raise ValueError(f"Duplicate parser name: {name}")

                    classes[name] = obj
                    logger.debug(f"Discovered parser class: {name} ({module_name})")
        return classes

    def _load_and_instantiate_parsers(self) -> dict[str, BaseParser]:
        """
        Instantiate parsers registered in yaml settings.
        """
        registry: dict[str, BaseParser] = {}
        parser_configs = settings.get("parsers", {})
        if not parser_configs:
            logger.warning("No parsers configured in settings.")
            return registry
        parser_names = parser_configs.keys()
        for name in parser_names:
            name = name.lower()
            if name not in self._discovered_classes:
                logger.warning(f"Parser '{name}' is configured but not discovered. Skipping instantiation.")
                continue
            parser_class = self._discovered_classes[name]
            try:
                registry[name] = parser_class()
                logger.info(f"Parser '{name}' instantiated successfully.")
            except Exception as e:
                logger.error(f"Failed to instantiate parser '{name}': {e}")
                continue
        return registry

    def get_parser(self, name: str) -> BaseParser:
        """
        Returns an instance of the parser with the given name.
        Raises KeyError if the parser is not found.
        """
        name = name.lower()
        if name not in self._registry:
            self._load_and_instantiate_parsers()
        if name not in self._registry:
            raise KeyError(f"Parser '{name}' not found in registry. Available parsers: {list(self._registry.keys())}")
        return self._registry[name]


parser_manager = ParserManager()
