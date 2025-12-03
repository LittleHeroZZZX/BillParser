from logging import getLogger

from .config import settings
from .models import ParserInput, ParserOutput
from .parsers.base import BaseParser
from .parsers.manager import ParserManager, parser_manager

logger = getLogger(__name__)


class Pipeline:
    name: str
    input_type: type[ParserInput]
    output_type: type[ParserOutput]

    def __init__(self, name: str, steps: list[BaseParser]):
        self.name = name
        self.steps = steps
        if not steps:
            raise ValueError("Pipeline must have at least one step")
        self.input_type = steps[0].input_type
        self.output_type = steps[-1].output_type

    async def run(self, input_data: ParserInput) -> ParserOutput:
        data = input_data
        for step in self.steps:
            if not isinstance(data, step.input_type):
                raise TypeError(
                    f"Step '{step.name}' expected input of type "
                    f"{step.input_type.__name__}, but got {type(data).__name__}"
                )
            data = await step.parse(data)
        assert isinstance(data, self.output_type), (
            f"Final output type mismatch: expected {self.output_type.__name__}, got {type(data).__name__}"
        )
        return data


class PipelineManager:
    def __init__(self, parser_manager: ParserManager):
        self.pipelines: dict[str, Pipeline] = {}
        self.parser_manager = parser_manager
        self._load_pipelines()

    def _load_pipelines(self):
        pipeline_configs = settings.get("pipelines", {})
        logger.info(f"Found {len(pipeline_configs)} pipeline configurations, names: {list(pipeline_configs.keys())}")
        for pipeline_name, config in pipeline_configs.items():
            logger.info(f"Loading pipeline '{pipeline_name}' with config: {config}")
            try:
                step_names = config.get("steps", [])
                steps = []
                for step_name in step_names:
                    parser = self.parser_manager.get_parser(step_name)
                    if parser is None:
                        raise ValueError(f"Parser '{step_name}' not found for pipeline '{pipeline_name}'")
                    steps.append(parser)
                pipeline = Pipeline(name=pipeline_name, steps=steps)
                self.pipelines[pipeline_name] = pipeline
                logger.info(
                    f"Successfully loaded pipeline '{pipeline_name}' with steps: {[step.name for step in steps]}"
                )
            except Exception as e:
                logger.error(f"Failed to load pipeline '{pipeline_name}': {e}")

    def get_pipeline(self, name: str) -> Pipeline | None:
        if name not in self.pipelines:
            self._load_pipelines()
        if name not in self.pipelines:
            logger.warning(f"Pipeline '{name}' not found")
            return None

        return self.pipelines.get(name)


pipeline_manager = PipelineManager(parser_manager=parser_manager)
