from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any

class IntentBase(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None

class IntentCreate(IntentBase):
    pass

class IntentUpdate(IntentBase):
    pass

class IntentOut(IntentBase):
    id: int

    model_config = ConfigDict(from_attributes=True)  
