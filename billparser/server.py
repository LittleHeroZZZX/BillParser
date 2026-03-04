from fastapi import Depends, FastAPI, File, Query, UploadFile

from .models import Bill, RawImage
from .pipeline import pipeline_manager
from .security import get_api_key

app = FastAPI(title="Bill Parser Service")


@app.post("/parse_image", tags=["Parsing"], dependencies=[Depends(get_api_key)])
async def parse_image(
    image: UploadFile = File(...),
    pipeline_name: str = Query("ocr_then_llm", description="Pipeline name"),
) -> Bill:
    """Endpoint to parse an image of a bill.

    Returns:
        dict: A placeholder response indicating successful parsing.
    """
    img_bytes = await image.read()
    pipeline = pipeline_manager.get_pipeline(pipeline_name)
    assert pipeline is not None, f"Pipeline '{pipeline_name}' not found"
    result = await pipeline.run(RawImage(img_bytes))
    assert isinstance(result, Bill), "Result is not of type Bill"
    return result
