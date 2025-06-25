from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException
from fastapi.responses import JSONResponse, FileResponse
import os
from image_process import process_image
from io import BytesIO
from PIL import Image
from pathlib import Path
import base64
import json
import uuid
import pika
import threading
import time
from fastapi.middleware.cors import CORSMiddleware
from image_process import start_consuming
from fastapi import BackgroundTasks

from jwt_handler import create_access_token, verify_token
from models import Token, LoginRequest, UserCreate
from models_db import User, Detection

from sqlalchemy.orm import Session
from db import SessionLocal
from models_db import User, Detection
from passlib.hash import bcrypt
from passlib.context import CryptContext
from datetime import datetime
from fastapi.staticfiles import StaticFiles
import detections



app = FastAPI()
app.mount("/images", StaticFiles(directory="images"), name="images")
app.include_router(detections.router)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        

def start_consuming_thread():
    thread = threading.Thread(target=start_consuming)
    thread.daemon = True  
    thread.start()

@app.on_event("startup")
async def startup_event():
    # Uygulama başlatıldığında RabbitMQ kuyruğunu dinlemeye başla
    start_consuming_thread()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)


def get_rabbitmq_connection():
    return pika.BlockingConnection(pika.ConnectionParameters('192.168.0.70',port=5673))

def send_to_queue(file_id: str, item_type: str):
    connection = get_rabbitmq_connection()
    channel = connection.channel()

    #kuyruk ol
    channel.queue_declare(queue="image_queue")

    #mesaj
    message = json.dumps({'file_id': file_id, 'type': item_type})
    channel.basic_publish(exchange='',
                        routing_key='image_queue',
                        body=message)

    connection.close()



@app.post("/app")
async def upload_image(file: UploadFile = File(...), item_type: str = Form(...),username: str = Depends(verify_token)):  
    try:
        file_id = str(uuid.uuid4())
        input_path = f"{file_id}.jpg"
        output_path = f"processed_{file_id}.jpg"
        json_path = f"{file_id}.json"

        contents = await file.read()
        with open(input_path, "wb") as f:
            f.write(contents)
        
        send_to_queue(file_id,item_type)
        
        return JSONResponse(
            content=file_id,
            status_code=200
        )
    except Exception as e:

        return JSONResponse(content={"message": f"Error: {str(e)}"}, status_code=500)


def delete_files(*file_paths: str):
    try:
        for path in file_paths:
            if Path(path).exists():
                os.remove(path)
    except Exception as e:
        print(f"Dosya silinirken hata:{e}")
    


@app.get("/app/{file_id}")
def get_processed_image(file_id: str,background_tasks: BackgroundTasks,timeout: int = 30, check_interval: float = 1.0,username: str = Depends(verify_token), db: Session = Depends(get_db)):

    file_path = f"images/processed_{file_id}.jpg"
    json_path = f"{file_id}.json"
    original_path = f"{file_id}.jpg"
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if Path(file_path).exists():
            with open(file_path, "rb") as image_file:
                image_base64 = base64.b64encode(image_file.read()).decode("utf-8")
            with open(json_path,"r") as json_file:
                prediction = json.load(json_file)
            
            #JSON Verisi AL
            detected_count = prediction.get("count",0)
            object_type = prediction.get("type","unknown")
            #kullanici bul
            user = db.query(User).filter(User.username == username).first()
            if user is None:
                raise HTTPException(status_code=404, detail="Kullanici bulunamadi")
            # Kayit olustur
            image_rel_path = f"images/processed_{file_id}.jpg"
            detection = Detection(
                user_id=user.id,
                timestamp=datetime.utcnow(),
                image_path=image_rel_path,
                detected_count=detected_count,
                object_type=object_type
            )
            db.add(detection)
            print("kayıt alındı.")
            db.commit()
                
            background_tasks.add_task(delete_files,json_path,original_path,f"processed_{file_id}.jpg")
            
            return JSONResponse(content={"status": "success", "data": {"image": image_base64,"prediction": detected_count}})
        
        time.sleep(check_interval)  # Belirtilen aralıkla bekle

    # Dosya hala yoksa hata döndür
    return JSONResponse(content={"error": "Görüntü dosyası bulunamadı"}, status_code=404)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@app.post("/login", response_model=Token)
def login(login_req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == login_req.username).first()
    print("geldi")
    if not user:
        raise HTTPException(status_code=401, detail="Gecersiz kullanici adi")

    if not pwd_context.verify(login_req.password, user.password):
        raise HTTPException(status_code=401, detail="Gecersiz sifre")

    token = create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}



"""
@app.post("/login", response_model=Token)
def login(login_req: LoginRequest):
    from jwt_handler import FAKE_USER  # yerel import
    print("geldi")
    if login_req.username != FAKE_USER["username"] or login_req.password != FAKE_USER["password"]:
        raise HTTPException(status_code=401, detail="Gecersiz kullanıcı adı veya sifre")
    token = create_access_token(data={"sub": login_req.username})
    return {"access_token": token, "token_type": "bearer"}
"""

@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Kullanc ad zaten var m kontrol et
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Kullanici adi zaten alinmis")

    # sifreyi hashle
    hashed_password = pwd_context.hash(user.password)

    # Yeni kullancy olutur ve veritabanna kaydet
    new_user = User(username=user.username, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "Kayit basarili"}









