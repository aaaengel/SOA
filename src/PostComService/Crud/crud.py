from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from Schemas.schema import Post, PostComment, PostPhoto
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

async def create_post(db: AsyncSession, data):
    try:
        post = Post(id=uuid.uuid4(), user_id = data.uuid_user, name = data.name, private = data.private, tags = data.tags)
        db.add(post)
        await db.commit()
        await db.refresh(post)
        return post
    except Exception as e:
        await db.rollback()
        raise e

async def get_post_by_id(db: AsyncSession, id: uuid) -> Post:
    res = await db.execute(select(Post).filter(Post.id == id))
    post = res.scalars().first()
    return post

async def get_posts_by_user_id(db: AsyncSession, id: uuid) -> list[Post]:
    res = await db.execute(select(Post).filter(Post.user_id == id))
    post = res.scalars().all()
    return post

async def update_post(db: AsyncSession, id: int, desc: str = None, name: str = None, tags: list = None):
    post = get_post_by_id(db, id)
    if not post:
        return None
    if name:
        post.name = name
    if desc:
        post.desc = desc
    if tags: 
        post.tags = tags
    await db.commit()
    await db.refresh(post)
    return post

async def delete_post(db: AsyncSession, id: int):
    post_obj = await get_post_by_id(db, id)
    if not post_obj:
        return False
    await db.delete(post_obj)
    await db.commit()
    return True

async def unlike(db: AsyncSession, id: uuid):
    post = get_post_by_id(db, id)
    post.likes_amount -= 1
    return post

async def like(db: AsyncSession, id: uuid):
    post = get_post_by_id(db, id)
    post.likes_amount += 1
    return post