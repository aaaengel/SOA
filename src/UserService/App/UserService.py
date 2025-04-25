from fastapi import FastAPI, Request, Depends, status, HTTPException, Response
import uvicorn
from Database.database import SessionLocal, engine
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr, Field
import jwt
import asyncio
from datetime import datetime, timedelta, timezone
import Crud.crud as cr
import uuid
from Schemas.schema import Base, User
from contextlib import asynccontextmanager
import logging
from fastapi.openapi.utils import get_openapi
import yaml
import os, json
from kafka import KafkaProducer
from datetime import datetime, timezone

producer = KafkaProducer(
    bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092'),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

async def create_tables():
    async with engine.begin() as conn:
        print(Base.metadata)
        await conn.run_sync(Base.metadata.create_all)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield

app = FastAPI(lifespan=lifespan)
ALGORITHM = "RS256"
with open("App/private.pem", "rb") as f:
    PRIVATE_KEY = f.read()

with open("App/public.pem", "rb") as f:
    PUBLIC_KEY = f.read()

async def get_db():
    async with SessionLocal() as db:
        yield db

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, PRIVATE_KEY, algorithm=ALGORITHM)

def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token')

def get_token(request: Request):
    token = request.cookies.get('token')
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token not found')
    return token

    
async def get_current_user(token: str = Depends(get_token), session: AsyncSession = Depends(get_db)):
    payload = verify_access_token(token)

    expire = payload.get('exp')
    expire_time = datetime.fromtimestamp(int(expire), tz=timezone.utc)
    if (not expire) or (expire_time < datetime.now(timezone.utc)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Токен истек')

    user_id = payload.get('id')
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='No id provided')

    user = await cr.get_user_by_id(session, uuid.UUID(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User not found')

    return user

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    login: str

class UserAuth(BaseModel):
    login: str
    password: str
class UserUpdate(BaseModel):
    first_name: str = ""
    last_name: str = ""
    phone_number: str = Field(
        ..., 
        pattern=r"^\+?[1-9]\d{1,14}$"
    )
    birth_date: datetime = datetime.now(timezone.utc)
    email: EmailStr = ""


class Token(BaseModel):
    access_token: str

@app.post("/register")
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    us = await cr.get_user_by_email(db, user.email)
    if us:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Already exists'
        )
    us_dict = user.model_dump()
    us = await cr.create_user(db, us_dict)
    event = {
    'client_id': str(us.id),
    'registration_date': datetime.now(timezone.utc).isoformat()
    }
    producer.send('client-registrations', event)
    producer.flush()
    return {'message': 'Register successfully!'}


@app.post("/login", response_model=Token)
async def login(response: Response, user: UserAuth, db: AsyncSession = Depends(get_db)):
    us = await cr.get_user_by_login(db, user.login)
    if not(us) or not(cr.pwd_context.verify(user.password, us.password)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = create_access_token(data={"id": str(us.id)})
    response.set_cookie(key="token", value=access_token, httponly=True)
    return {'access_token': access_token}
@app.get("/me")
async def whoami(user: User = Depends(get_current_user)):
    return user

@app.get("/hello")
async def hello():
    return {"status": "ok"}
# @app.get("/wait")
# async def whoami(db: AsyncSession = Depends(get_db)):
#     await asyncio.sleep(10)
#     await db.commit()
@app.put("/me/update")
async def whoami(new_data: UserUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user.name = new_data.first_name if new_data.first_name else user.first_name
    user.second_name = new_data.last_name if new_data.last_name else user.last_name
    user.phone = new_data.phone_number if new_data.phone_number else user.phone_number
    user.birthday = new_data.birth_date.replace(tzinfo=None) if new_data.birth_date else user.birth_date
    user.email = new_data.email if new_data.email else user.email
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
# @app.get("/openapi.yaml", include_in_schema=False)
# def get_openapi_yaml():
#     openapi_schema = get_openapi(
#         title = "UserService",
#         version="1.0.0",
#         routes=app.routes
#     )
#     yaml_schema = yaml.dump(openapi_schema, sort_keys=False, allow_unicode=True)
#     return Response(content=yaml_schema, media_type="application/x-yaml")


# @app.get("/user/{username}")
# async def get_user(username: str):
#     pass

# @app.get("/user/me")
# async def get_me(username: str):
#     pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("App.UserService:app", host="localhost", port=5001, reload=True)