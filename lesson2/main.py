from fastapi import FastAPI,HTTPException,Depends
from sqlalchemy.ext.asyncio import AsyncSession
from crud import get_books,get_book,add_book,update_book,delete_book,update_user_role
from database import engine,Base,get_db
from schemas import BookCreate,BookResponse,UserCreate,UserResponse,UserLogin,Token,RoleUpdate
from auth import register,login,get_user,require_roles
from fastapi.security import OAuth2PasswordRequestForm

app=FastAPI()

@app.on_event('startup')
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get('/books',response_model=list[BookResponse])
async def read_books(db:AsyncSession = Depends(get_db),current_user=Depends(get_user)):
    return await get_books(db)

@app.post('/books',response_model=BookResponse)
async def create_book(
    data:BookCreate,
    db:AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(["moderator","admin"]))
):
    return await add_book(data,db)

@app.get('/book/{book_id}',response_model=BookResponse)
async def read_book(book_id:int,db:AsyncSession=Depends(get_db),current_user=Depends(get_user)):
    book=await get_book(db,book_id)

    if not book:
        raise HTTPException(status_code=404,detail='Book not found')
    return book

@app.delete('/book/{book_id}')
async def remove_book(
    book_id:int,
    db:AsyncSession=Depends(get_db),
    current_user=Depends(require_roles(["admin"]))
):
    return await delete_book(book_id,db)

@app.patch('/book/{book_id}',response_model=BookResponse)
async def edit_book(
    book_id:int,
    data:BookCreate,
    db:AsyncSession=Depends(get_db),
    current_user=Depends(require_roles(["moderator","admin"]))
):
    book = await update_book(book_id, data, db)
    if not book:
        raise HTTPException(status_code=404, detail='Book not found')
    return book

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