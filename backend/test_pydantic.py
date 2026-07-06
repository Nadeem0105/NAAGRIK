from pydantic import BaseModel, ConfigDict
from typing import Optional

class MyModel:
    def __init__(self):
        self.bbox_south = 10.0
        
    @property
    def bbox(self):
        return {"south": self.bbox_south}

class MySchema(BaseModel):
    bbox: Optional[dict] = None
    
    model_config = ConfigDict(from_attributes=True)

obj = MyModel()
schema = MySchema.model_validate(obj)
print(schema.bbox)
