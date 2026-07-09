from fastapi import HTTPException,Depends
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


def require_role(role: str):
    return require_roles([role])