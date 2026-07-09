from sqlalchemy import Integer,String,Float,Boolean
from sqlalchemy.orm import Mapped,mapped_column
from database import Base

class Book(Base):
    __tablename__ = 'books'

    id:Mapped[int]=mapped_column(Integer, primary_key=True, autoincrement=True)
    title:Mapped[str]=mapped_column(String)
    author:Mapped[str]=mapped_column(String)
    is_available:Mapped[bool]=mapped_column(Boolean,default=True)
    price:Mapped[float]=mapped_column(Float)

class User(Base):
    __tablename__='users'
    id:Mapped[int]=mapped_column(Integer, primary_key=True, autoincrement=True)
    username:Mapped[str]=mapped_column(String(100),unique=True)
    email:Mapped[str]=mapped_column(String(100),unique=True)
    password:Mapped[str]=mapped_column(String)
    role: Mapped[str] = mapped_column(String(50), default="user")