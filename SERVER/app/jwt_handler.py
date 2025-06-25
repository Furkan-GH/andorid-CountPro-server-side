# auth/jwt_handler.py


from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
import time
from db import SessionLocal
from models_db import User
from sqlalchemy.orm import Session


SECRET_KEY = "secretfurkantoken"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
FAKE_USER = {"username": "furkan", "password": "1234"}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = time.time() + (ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Gecersiz token")

        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise HTTPException(status_code=401, detail="Kullanici adi yanlis")

        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Gecersiz token")


"""
def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username != FAKE_USER["username"]:
            raise HTTPException(status_code=401, detail="Kullanici adi yanlis")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Gecersiz token")
"""
