import asyncio
from pathlib import Path

import typer
import uvicorn

from .models import Bill, RawImage

app = typer.Typer(help="BillParser 命令行工具")


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Host to bind"),
    port: int = typer.Option(8000, help="Port to bind"),
    reload: bool = typer.Option(False, help="Enable auto-reload"),
):
    """
    启动 Web API 服务
    """
    typer.echo(f"Starting server on {host}:{port}")
    uvicorn.run("billparser.server:app", host=host, port=port, reload=reload)


@app.command()
def parse_file(
    filepath: Path = typer.Argument(..., help="图片或文本文件的路径", exists=True),
    pipeline: str = typer.Option("ocr_then_llm", help="使用的流水线名称"),
):
    """
    解析单个文件 (支持本地图片测试)
    """
    typer.echo(f"Processing file: {filepath}")
    from billparser.pipeline import pipeline_manager

    pipeline_instance = pipeline_manager.get_pipeline(pipeline)
    assert pipeline_instance is not None, f"Pipeline '{pipeline}' not found"

    # 简单的文件类型判断
    initial_type = RawImage
    with open(filepath, "rb") as f:
        data = f.read()

    try:
        result = asyncio.run(pipeline_instance.run(initial_type(data)))
        assert isinstance(result, Bill), "解析结果不是 Bill 类型"
        typer.secho("Parsed Bill:", fg=typer.colors.GREEN)
        typer.echo(result.model_dump_json(indent=4, ensure_ascii=False))

    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)


@app.command()
def process_folder(
    folder: Path = typer.Argument(..., help="文件夹路径", exists=True, file_okay=False),
    output: Path = typer.Option(Path("output.csv"), help="导出 CSV 路径"),
):
    """
    (Placeholder) 批量处理文件夹中的图片并导出
    """
    typer.echo(f"TODO: Scanning folder {folder} and exporting to {output}")


if __name__ == "__main__":
    app()
