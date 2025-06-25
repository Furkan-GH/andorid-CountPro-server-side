# auth/models.py


from pydantic import BaseModel
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class LoginRequest(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    password: str

class DetectionResponse(BaseModel):
    id: int
    timestamp: str
    object_type: str
    detected_count: int
    image_url: str  # image_path -> image_url 

    class Config:
        from_attributes = True
