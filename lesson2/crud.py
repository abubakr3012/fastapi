from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from securety import hash_password,verify_password,create_access_token
from models import Book,User
from schemas import BookCreate,UserCreate,UserLogin,UserResponse


async def get_books(db: AsyncSession):
    result = await db.execute(select(Book))
    return result.scalars().all()


async def add_book(data: BookCreate, db: AsyncSession):
    new_book = Book(**data.model_dump())

    db.add(new_book)
    await db.commit()
    await db.refresh(new_book)

    return new_book


async def get_book(db: AsyncSession, id: int):
    result = await db.execute(
        select(Book).where(Book.id == id)
    )

    return result.scalar_one_or_none()


async def delete_book(book_id: int, db: AsyncSession):

    result = await db.execute(
        select(Book).where(Book.id == book_id)
    )

    book = result.scalar_one_or_none()

    if book is None:
        return None

    await db.delete(book)
    await db.commit()

    return {"message": "Book Deleted"}


async def update_book(book_id: int, data: BookCreate, db: AsyncSession):

    result = await db.execute(
        select(Book).where(Book.id == book_id)
    )

    book = result.scalar_one_or_none()

    if book is None:
        return None


    if data.title is not None:
        book.title = data.title

    if data.author is not None:
        book.author = data.author

    if data.price is not None:
        book.price = data.price


    await db.commit()
    await db.refresh(book)

    return book

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