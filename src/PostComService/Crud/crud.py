from sqlalchemy.orm import Session
from Schemas.schema import Post
import uuid
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

def create_post_sync(db: Session, data):
    try:
        post = Post(
            id=uuid.uuid4(),
            user_id=uuid.UUID(data.uuid_user.value),
            name=data.name,
            private=data.private,
            tags=data.tags,
        )
        db.add(post)
        db.commit()
        db.refresh(post)
        return post
    except Exception as e:
        db.rollback()
        raise e

def get_post_by_id_sync(db: Session, id: uuid.UUID) -> Post:
    return db.query(Post).filter(Post.id == id).first()

def get_posts_by_user_id_sync(db: Session, id: uuid.UUID) -> list[Post]:
    return db.query(Post).filter(Post.user_id == id).all()

def update_post_sync(db: Session, id: uuid.UUID, name: str = None, desc: str = None, tags: list = None):
    post = get_post_by_id_sync(db, id)
    if not post:
        return None
    if name:
        post.name = name
    if desc:
        post.desc = desc
    if tags:
        post.tags = tags
    db.commit()
    db.refresh(post)
    return post

def delete_post_sync(db: Session, id: uuid.UUID):
    post = get_post_by_id_sync(db, id)
    if not post:
        return False
    db.delete(post)
    db.commit()
    return True

def like_post_sync(db: Session, id: uuid.UUID):
    post = get_post_by_id_sync(db, id)
    post.likes_amount += 1
    db.commit()
    db.refresh(post)
    return post

def unlike_post_sync(db: Session, id: uuid.UUID):
    post = get_post_by_id_sync(db, id)
    post.likes_amount -= 1
    db.commit()
    db.refresh(post)
    return post