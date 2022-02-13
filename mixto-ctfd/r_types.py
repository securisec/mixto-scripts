from typing import List
from pydantic import BaseModel

class MixtoConfig(BaseModel):
    api_key: str
    categories: List[str]
    host: str
    workspace: str

class CTFdChallenge(BaseModel):
    name: str
    category: str

class CTFdResponse(BaseModel):
    success: bool
    data: List[CTFdChallenge]

class MixtoEntry(BaseModel):
    title: str
    category: str