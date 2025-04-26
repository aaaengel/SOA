import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import event
from Database.database import engine, SessionLocal
from Crud import crud as cr
from App.UserService import (
    create_access_token,
    verify_access_token,
    ALGORITHM,
    PRIVATE_KEY,
)
from Schemas.schema import User
import asyncio
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="function")
async def db():
    async with engine.connect() as connection:
        transaction = await connection.begin()
        async with SessionLocal(bind=connection) as session:
            await session.begin_nested()
            @event.listens_for(session.sync_session, "after_transaction_end")
            def restart_savepoint(sess, trans):
                if trans.nested and not sess.in_nested_transaction():
                    sess.begin_nested()

            yield session
        await transaction.rollback()

@pytest.mark.asyncio
async def test_create_and_get_user(db: AsyncSession):
    unique_id = uuid.uuid4().hex[:5]
    user_data = {
        "login": f"{unique_id}",
        "email": f"{unique_id}@example.com",
        "password": "secretpassword"
    }
    new_user = await cr.create_user(db, user_data)
    assert new_user.login == user_data["login"]
    assert new_user.email == user_data["email"]

    fetched_user = await cr.get_user_by_id(db, new_user.id)
    assert fetched_user is not None
    assert fetched_user.id == new_user.id

    user_by_login = await cr.get_user_by_login(db, new_user.login)
    assert user_by_login is not None
    assert user_by_login.id == new_user.id

    user_by_email = await cr.get_user_by_email(db, new_user.email)
    assert user_by_email is not None
    assert user_by_email.id == new_user.id

@pytest.mark.asyncio
async def test_update_user(db: AsyncSession):
    unique_id = uuid.uuid4().hex[:5]
    user_data = {
        "login": f"{unique_id}",
        "email": f"{unique_id}@example.com",
        "password": "secret"
    }
    new_user = await cr.create_user(db, user_data)
    
    updated_email = f"{unique_id}@example.com"
    updated_user = await cr.update_user(db, new_user.id, name="New Name Prod", email=updated_email)
    assert updated_user is not None
    assert updated_user.name == "New Name Prod"
    assert updated_user.email == updated_email

def test_token_creation_and_verification():
    payload = {"id": str(uuid.uuid4())}
    token = create_access_token(payload)
    verified_payload = verify_access_token(token)
    assert "id" in verified_payload
    assert "exp" in verified_payload
    assert verified_payload["id"] == payload["id"]

def test_invalid_token():
    invalid_token = "invalid.token.string"
    result = verify_access_token(invalid_token)
    assert isinstance(result, HTTPException)
    assert result.detail == "Invalid token"

def test_expired_token():
    past = datetime.now(timezone.utc) - timedelta(days=1)
    payload = {"id": str(uuid.uuid4()), "exp": past}
    expired_token = jwt.encode(payload, PRIVATE_KEY, algorithm=ALGORITHM)
    result = verify_access_token(expired_token)
    assert isinstance(result, HTTPException)
    assert result.detail == "Invalid token"
