import json
from pydantic import BaseModel


async def serialize_model_to_json(model: BaseModel) -> str:
    """
    Serialize model to json format

    Example:
        ```python
        async def sse_stream():
            try:
                async for chunk in ai_service.generate_stream(
                    prompt=request.prompt,
                    provider=request.provider,
                    model=request.model,
                ):
                    # Serialize chunk to JSON
                    yield await serialize_model_to_json(chunk)
        ```
    """
    if hasattr(model, "model_dump_json"):
        return f"data: {model.model_dump_json()}\n\n"
    elif hasattr(model, "model_dump"):
        return f"data: {json.dumps(model.model_dump())}\n\n"
    else:
        # Fallback for dict
        return f"data: {json.dumps(model)}\n\n"
