from pydantic import BaseModel

class BookCreate(BaseModel):
    title: str | None = None
    author: str | None = None
    price: float | None = None


class BookResponse(BaseModel):
    id: int
    title: str
    author: str
    price: float

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

class RoleUpdate(BaseModel):
    role:str

class Token(BaseModel):
    access_token:str
    token_type:str