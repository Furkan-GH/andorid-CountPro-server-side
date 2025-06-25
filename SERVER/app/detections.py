from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime


from models_db import Detection
from jwt_handler import verify_token
from models import DetectionResponse
from db import SessionLocal
from models_db import User

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter()

@router.get("/detections", response_model=List[DetectionResponse])
def get_detections(
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)  
):
    user = db.query(User).filter(User.username == current_user).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Kullanici bulunamadi")

    detections = db.query(Detection).filter(Detection.user_id == user.id).all()

    result = []
    for d in detections:
        result.append({
            "id": d.id,
            "timestamp": d.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "object_type": d.object_type,
            "detected_count": d.detected_count,
            "image_url": d.image_path  
        })


    return result
