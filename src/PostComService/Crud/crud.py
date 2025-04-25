from sqlalchemy.orm import Session
from Schemas.schema import Post, PostComment
import uuid
import logging
from datetime import datetime

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

def view_post_sync(db: Session, post_id: uuid.UUID):
    post = get_post_by_id_sync(db, post_id)
    post.views_amount += 1
    db.commit()
    db.refresh(post)
    return post

def like_post_sync(db: Session, post_id: uuid.UUID):
    post = get_post_by_id_sync(db, post_id)
    post.likes_amount += 1
    db.commit()
    db.refresh(post)
    return post

def comment_post_sync(db: Session, post_id: uuid.UUID, user_id: uuid.UUID, content: str, replied: uuid.UUID = None):
    comment = PostComment(
        comment_id=uuid.uuid4(),
        related_post=post_id,
        commenter_id=user_id,
        content=content,
        replied=replied,
        posted_at=datetime.now()
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment

def get_comments_paginated_sync(db: Session, post_id: uuid.UUID, offset: int, limit: int):
    return db.query(PostComment)\
        .filter(PostComment.related_post == post_id)\
        .order_by(PostComment.posted_at)\
        .offset(offset)\
        .limit(limit)\
        .all()