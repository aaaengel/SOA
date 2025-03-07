from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from Schemas.schema import User, UserSubs, ActivityLog
from passlib.context import CryptContext
from fastapi import HTTPException
import uuid
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Формат вывода логов
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

# Обработчик вывода в консоль
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# Добавляем обработчик к логгеру
logger.addHandler(console_handler)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_user(db: AsyncSession, data: dict):
    try:
        new_user = User(login=data["login"], email=data["email"], password = pwd_context.hash(data["password"]), id = uuid.uuid4())
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка сервера при регистрации: {str(e)}")

async def get_user_by_id(db: AsyncSession, id: uuid):
    res = await db.execute(select(User).filter(User.id == id))
    user = res.scalars().first()
    return user

async def get_user_by_login(db: AsyncSession, login: str):
    res = await db.execute(select(User).filter(User.login == login))
    user = res.scalars().first()
    return user

async def get_user_by_email(db: AsyncSession, email: str):
    res = await db.execute(select(User).filter(User.email == email))
    user = res.scalars().first()
    return user

async def update_user(db: AsyncSession, user_id: int, name: str = None, email: str = None):
    user = await db.execute(select(User).filter(User.id == user_id))
    user = user.scalars().first()
    if not user:
        return None
    if name:
        user.name = name
    if email:
        user.email = email
    await db.commit()
    await db.refresh(user)
    return user