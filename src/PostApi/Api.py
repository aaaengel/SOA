from fastapi import FastAPI, HTTPException, Depends, Request, Response, Cookie
import uvicorn
import grpc
import asyncio
import json
import uuid
import jwt
from datetime import datetime, timezone
from google.protobuf.json_format import MessageToDict

import post_pb2 as post_pb2
import post_pb2_grpc as post_pb2_grpc

app = FastAPI()
ALGORITHM = "RS256"
with open("public.pem", "rb") as f:
    PUBLIC_KEY = f.read().decode("utf-8")

def verify_access_token(token: str):
    try:
        print(token)
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def decode_token(token: str) -> dict:
    payload = verify_access_token(token)
    expire = payload.get("exp")
    if not expire:
        raise HTTPException(status_code=401, detail="Token missing exp")
    expire_time = datetime.fromtimestamp(int(expire), tz=timezone.utc)
    if expire_time < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Token expired")
    return payload

def get_user_id(req: Request):
    token = req.cookies.get("token")
    payload = decode_token(token)
    user_id = payload.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="No user id in token")
    return user_id

GRPC_POST_SERVICE = "postservice:50051"
grpc_channel = grpc.insecure_channel(GRPC_POST_SERVICE)
stub = post_pb2_grpc.PostsStub(grpc_channel)

@app.post("/posts")
async def create_post(request: Request):
    user_id = get_user_id(request)
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    
    grpc_post = post_pb2.Post(
        name=body.get("name", ""),
        desc=body.get("desc", ""),
        private=body.get("private", False),
        tags=body.get("tags", []),
        uuid_user=post_pb2.UUID(value=str(user_id))
    )
    try:
        response = await asyncio.to_thread(stub.CreatePost, grpc_post)
        return MessageToDict(response)
    except grpc.RpcError as e:
        raise HTTPException(status_code=e.code().value[0], detail=e.details())

@app.get("/posts/{post_id}")
async def get_post(post_id: str):
    try:
        grpc_uuid = post_pb2.UUID(value=post_id)
        response = await asyncio.to_thread(stub.GetById, grpc_uuid)
        return MessageToDict(response)
    except grpc.RpcError as e:
        raise HTTPException(status_code=e.code().value[0], detail=e.details())

@app.get("/posts/user/{user_id}")
async def get_posts_by_user(user_id: str):
    try:
        grpc_uuid = post_pb2.UUID(value=user_id)
        posts = []
        def get_posts_stream():
            return list(stub.GetPosts(grpc_uuid))
        posts_stream = await asyncio.to_thread(get_posts_stream)
        for post_msg in posts_stream:
            posts.append(MessageToDict(post_msg))
        return posts
    except grpc.RpcError as e:
        raise HTTPException(status_code=e.code().value[0], detail=e.details())

@app.put("/posts/{post_id}")
async def update_post(post_id: str, request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    
    update_msg = post_pb2.UpdatePostMsg(
        uuid=post_pb2.UUID(value=post_id),
        name=body.get("name", ""),
        desc=body.get("desc", ""),
        private=body.get("private", False),
        tags=body.get("tags", [])
    )
    try:
        response = await asyncio.to_thread(stub.UpdatePost, update_msg)
        return MessageToDict(response)
    except grpc.RpcError as e:
        raise HTTPException(status_code=e.code().value[0], detail=e.details())

@app.delete("/posts/{post_id}")
async def delete_post(post_id: str):
    try:
        grpc_uuid = post_pb2.UUID(value=post_id)
        response = await asyncio.to_thread(stub.DeletePost, grpc_uuid)
        return MessageToDict(response)
    except grpc.RpcError as e:
        raise HTTPException(status_code=e.code().value[0], detail=e.details())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
