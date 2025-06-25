from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from db import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)  # bcrypt hash


class Detection(Base):
    __tablename__ = "detections"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    image_path = Column(Text)
    detected_count = Column(Integer)
    object_type = Column(String)
