from typing import Optional
from pydantic import BaseModel


class OperationResponse(BaseModel):
    """Generic response for operations"""

    success: bool
    message: str
    previous_value: Optional[str] = None
    new_value: Optional[str] = None
