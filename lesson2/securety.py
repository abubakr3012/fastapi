import os
from dotenv import load_dotenv
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta

load_dotenv()

SEKRET_KEY = os.getenv('SEKRET_KEY')
ALGORITM = 'HS256'
ACCESS_TOKEN_EXPIRE_REFRESH = 30

pwd_context = CryptContext(schemes=['argon2'])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(password: str, hash_password: str):
    return pwd_context.verify(password, hash_password)

def create_access_token(data: dict):
    payload = data.copy()
    payload['exp'] = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_REFRESH)
    return jwt.encode(payload, SEKRET_KEY, ALGORITM)

def decode_access_token(token: str):
    try:
        return jwt.decode(token, SEKRET_KEY, algorithms=[ALGORITM])
    except JWTError:
        raise HTTPException(status_code=401, detail='Error in validate(decode_access_token)')