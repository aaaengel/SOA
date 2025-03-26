from datetime import datetime
from sqlalchemy import Column, Integer, String, UUID, TIMESTAMP, BOOLEAN, ForeignKey
from Database.database import Base

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

class UserSubs(Base):
    __tablename__ = "user_subs"

    sub_id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    name = Column(String(20), nullable=False)
    sub_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    created_at = Column(TIMESTAMP, default=datetime.now())
    status = Column(BOOLEAN, default=False, onupdate=True)

class ActivityLog(Base):
    __tablename__ = "activity"

    log_id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    action = Column(String(20))
    action_time = Column(TIMESTAMP, default=datetime.now())
    ip_address = Column(String(20), nullable=True)
    user_agent = Column(String(20), nullable=True)