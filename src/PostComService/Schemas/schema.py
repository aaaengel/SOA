from datetime import datetime
from sqlalchemy import Column, Integer, String, TIMESTAMP, BOOLEAN, ForeignKey, ARRAY, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
from Database.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    login = Column(String(20), nullable=False)
    name = Column(String(20), nullable=True)
    second_name = Column(String(20), nullable=True)
    password = Column(String(100), nullable=False)
    email = Column(String(50), unique=True, index=True, nullable=False)
    phone = Column(String(20), unique=True, index=True)
    created_at = Column(TIMESTAMP, default=datetime.now())
    updated_at = Column(TIMESTAMP, default=datetime.now(), onupdate=datetime.now())
    online_at = Column(TIMESTAMP, default=datetime.now(), onupdate=datetime.now())
    birthday = Column(TIMESTAMP)
    status = Column(BOOLEAN, default=False, onupdate=True)
    
class Post(Base):
    __tablename__ = "posts"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    name = Column(String(20), nullable=True)
    desc = Column(String(1000), nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.now())
    updated_at = Column(TIMESTAMP, default=datetime.now(), onupdate=datetime.now())
    private = Column(BOOLEAN, default=False, onupdate=True)
    tags = Column(ARRAY(String))
    likes_amount = Column(Integer, default=0)
    views_amount = Column(Integer, default=0)

class PostPhoto(Base):
    __tablename__ = "post_photo"

    photo_id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    related_post = Column(UUID(as_uuid=True), ForeignKey("posts.id"), index=True)
    photo = Column(LargeBinary)
    place = Column(String(30), nullable=True)
    file_size = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)


class PostComment(Base):
    __tablename__ = "post_comments"

    comment_id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    related_post = Column(UUID(as_uuid=True), ForeignKey("posts.id"), index=True)
    commenter_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    replied = Column(UUID(as_uuid=True), nullable=True)
    likes_amount = Column(Integer)
    posted_at = Column(TIMESTAMP, default=datetime.now())
    content = Column(String(500), nullable=True)