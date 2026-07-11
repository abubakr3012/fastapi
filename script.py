import os

prefix = "lesson"

crud="""from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from securety import hash_password
from models import User
from schemas import UserCreate



async def create_user(data:UserCreate,db:AsyncSession):
    password=hash_password(data.password)
    new_user=User(username=data.username,email=data.email,password=password)

    db.add(new_user)

    await db.commit()

    await db.refresh(new_user)

    return new_user

async def get_user_by_email(email:str,db:AsyncSession):
    user=await db.execute(select(User).where(User.email==email))
    return user.scalar_one_or_none()

async def get_user_by_username(username:str,db:AsyncSession):
    user=await db.execute(select(User).where(User.username==username))
    return user.scalar_one_or_none()

async def search_user_by_id(user_id:int,db:AsyncSession):
    user=await db.execute(select(User).where(User.id==user_id))
    return user.scalar_one_or_none()


"""

database="""from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "postgresql+asyncpg://postgres:1234@localhost:5432/books"

engine = create_async_engine(
    DATABASE_URL,
    echo=True
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


class Base(DeclarativeBase):
    pass
"""

main="""from fastapi import FastAPI,HTTPException,Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import engine,Base,get_db
from schemas import UserCreate,UserResponse,UserLogin,Token,RoleUpdate
from auth import register,login,get_user,require_roles
from fastapi.security import OAuth2PasswordRequestForm

app=FastAPI()

@app.on_event('startup')
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.post('/register',response_model=UserResponse)
async def register_user(data:UserCreate,db:AsyncSession=Depends(get_db)):
    return await register(data,db)

@app.post('/login',response_model=Token)
async def login_user(form_data:OAuth2PasswordRequestForm=Depends(),db:AsyncSession=Depends(get_db)):
    return await login(form_data,db)

@app.get('/me',response_model=UserResponse)
async def me(current_user=Depends(get_user)):
    return current_user

@app.patch('/users/{user_id}/role',response_model=UserResponse)
async def change_user_role(
    user_id:int,
    data:RoleUpdate,
    db:AsyncSession=Depends(get_db),
    current_user=Depends(require_roles(["admin"]))
):
    allowed_roles=["user","moderator","admin"]

    if data.role not in allowed_roles:
        raise HTTPException(status_code=400,detail=f'Role must be one of {allowed_roles}')

    updated_user=await update_user_role(user_id,data.role,db)

    if updated_user is None:
        raise HTTPException(status_code=404,detail='User not found')

    return updated_user
"""

models="""from sqlalchemy import Integer,String,Float,Boolean
from sqlalchemy.orm import Mapped,mapped_column
from database import Base


class User(Base):
    __tablename__='users'
    id:Mapped[int]=mapped_column(Integer, primary_key=True, autoincrement=True)
    username:Mapped[str]=mapped_column(String(100),unique=True)
    email:Mapped[str]=mapped_column(String(100),unique=True)
    password:Mapped[str]=mapped_column(String)
    role: Mapped[str] = mapped_column(String(50), default="user")

"""

schemas="""from pydantic import BaseModel

class UserCreate(BaseModel):
    username:str
    email:str
    password:str

class UserResponse(BaseModel):
    id:int
    username:str
    email:str
    role:str

class UserLogin(BaseModel):
    username:str
    password:str

class Token(BaseModel):
    access_token:str
    token_type:str

"""

auth="""from fastapi import HTTPException,Depends
from crud import get_user_by_email,get_user_by_username,create_user,search_user_by_id
from database import get_db
from schemas import UserLogin,UserCreate
from sqlalchemy.ext.asyncio import AsyncSession
from securety import verify_password,create_access_token,oauth2_scheme,decode_access_token


async def register(data:UserCreate,db:AsyncSession):
    email_exist=await get_user_by_email(data.email,db)
    username_exist=await get_user_by_username(data.username,db)

    if email_exist:
        raise HTTPException(status_code=400,detail='Email already exists')

    if username_exist:
        raise HTTPException(status_code=400,detail='Username already exists')

    return await create_user(data,db)

async def login(data:UserLogin,db:AsyncSession):
    user_exists=await get_user_by_username(data.username,db)

    if not user_exists:
        raise HTTPException(status_code=400,detail='Invalid exists')

    if not verify_password(data.password,user_exists.password):
        raise HTTPException(status_code=400,detail='Invalid verify')

    token=create_access_token(
        {
            "sub":str(user_exists.id)
        }
    )
    return {"access_token":token,"token_type":"bearer"}

async def get_user(token:str=Depends(oauth2_scheme),db:AsyncSession=Depends(get_db)):
    payload=decode_access_token(token)
    user_id=payload.get('sub')

    if user_id is None:
        raise HTTPException(status_code=401,detail='Invalid token')
    user=await search_user_by_id(int(user_id),db)

    if user is None:
        raise HTTPException(status_code=401,detail='User not found')
    return user


def require_roles(allowed_roles: list[str]):
    def role_checker(current_user=Depends(get_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail='Permission denied')
        return current_user
    return role_checker

"""

securety="""import os
from dotenv import load_dotenv
from fastapi import HTTPException
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

"""

folders = os.listdir()

numbers = []

for folder in folders:
    if folder.startswith(prefix):
        try:
            number = int(folder.replace(prefix, ""))
            numbers.append(number)
        except:
            pass

if numbers:
    next_number = max(numbers) + 1
else:
    next_number = 1


new_folder = f"{prefix}{next_number}"

os.makedirs(new_folder)

main_file = os.path.join(new_folder, "main.py")
models_file = os.path.join(new_folder, "models.py")
database_file=os.path.join(new_folder,'database.py')
schemas_file=os.path.join(new_folder,'schemas.py')
crud_file=os.path.join(new_folder,'crud.py')
auth_file=os.path.join(new_folder,'auth.py')
securety_file=os.path.join(new_folder,'securety.py')

with open(main_file, "w", encoding="utf-8") as file:
    file.write(f"{main}\n")

with open(models_file, "w", encoding="utf-8") as file:
    file.write(f"{models}\n")

with open(database_file, "w", encoding="utf-8") as file:
    file.write(f"{database}\n")

with open(schemas_file, "w", encoding="utf-8") as file:
    file.write(f"{schemas}\n")

with open(crud_file, "w", encoding="utf-8") as file:
    file.write(f"{crud}\n")

with open(auth_file, "w", encoding="utf-8") as file:
    file.write(f"{auth}\n")

with open(securety_file, "w", encoding="utf-8") as file:
    file.write(f"{securety}\n")


print(f"Создано: {new_folder} with all files")
