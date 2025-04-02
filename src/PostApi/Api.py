from fastapi import FastAPI, HTTPException, Request, status, Response
import uvicorn
import grpc
from grpc import StatusCode
import post_pb2 as post_pb2
import post_pb2_grpc as post_pb2_grpc
from google.protobuf.json_format import MessageToDict
from datetime import datetime, timezone
import jwt
from fastapi.openapi.utils import get_openapi
import yaml

app = FastAPI()

ALGORITHM = "RS256"
with open("public.pem", "rb") as f:
    PUBLIC_KEY = f.read().decode("utf-8")

grpc_to_http = {
    StatusCode.OK: 200,
    StatusCode.CANCELLED: 499,
    StatusCode.UNKNOWN: 500,
    StatusCode.INVALID_ARGUMENT: 400,
    StatusCode.DEADLINE_EXCEEDED: 504,
    StatusCode.NOT_FOUND: 404,
    StatusCode.ALREADY_EXISTS: 409,
    StatusCode.PERMISSION_DENIED: 403,
    StatusCode.RESOURCE_EXHAUSTED: 429,
    StatusCode.FAILED_PRECONDITION: 412,
    StatusCode.ABORTED: 409,
    StatusCode.OUT_OF_RANGE: 400,
    StatusCode.UNIMPLEMENTED: 501,
    StatusCode.INTERNAL: 500,
    StatusCode.UNAVAILABLE: 503,
    StatusCode.DATA_LOSS: 500,
    StatusCode.UNAUTHENTICATED: 401,
}

def verify_access_token(token: str):
    try:
        payload = jwt.decode(
            token,
            PUBLIC_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": True}
        )
        return payload
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )

def decode_token(token: str) -> str:
    payload = verify_access_token(token)
    expire = payload.get("exp")
    if not expire:
        raise HTTPException(status_code=401, detail="Token missing exp")
    expire_time = datetime.fromtimestamp(int(expire), tz=timezone.utc)
    if expire_time < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Token expired")
    user_id = payload.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="No user id in token")
    return user_id

def get_user_id(req: Request) -> str:
    token = req.cookies.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="Token not found in cookies")
    return decode_token(token)

GRPC_POST_SERVICE = "localhost:50051"
channel = grpc.insecure_channel(GRPC_POST_SERVICE)
stub = post_pb2_grpc.PostsStub(channel)

@app.post("/posts")
async def create_post(request: Request):
    user_id = get_user_id(request)
    body = await request.json()

    grpc_post = post_pb2.Post(
        name=body.get("name", ""),
        desc=body.get("desc", ""),
        private=body.get("private", False),
        tags=body.get("tags", []),
        uuid_user=post_pb2.UUID(value=str(user_id))
    )

    try:
        response = stub.CreatePost(grpc_post)
        return MessageToDict(response)
    except grpc.RpcError as e:
        raise HTTPException(status_code=e.code().value[0], detail=e.details())

@app.get("/posts/{post_id}")
def get_post(post_id: str):
    try:
        grpc_uuid = post_pb2.UUID(value=post_id)
        print(grpc_uuid.value)
        response = stub.GetById(grpc_uuid)
        return MessageToDict(response)
    except grpc.RpcError as e:
        print("ALARM ERROR")
        print(str(e))
        code = grpc_to_http.get(e.code())
        raise HTTPException(status_code=code, detail=e.details())

@app.get("/posts/user/{user_id}")
def get_posts_by_user(user_id: str):
    try:
        grpc_uuid = post_pb2.UUID(value=user_id)
        posts = [MessageToDict(post) for post in stub.GetPosts(grpc_uuid)]
        return posts
    except grpc.RpcError as e:
        raise HTTPException(status_code=e.code().value[0], detail=e.details())

@app.put("/posts/{post_id}")
async def update_post(post_id: str, request: Request):
    body = await request.json()
    update_msg = post_pb2.UpdatePostMsg(
        uuid=post_pb2.UUID(value=post_id),
        name=body.get("name", ""),
        desc=body.get("desc", ""),
        private=body.get("private", False),
        tags=body.get("tags", [])
    )
    try:
        response = stub.UpdatePost(update_msg)
        return MessageToDict(response)
    except grpc.RpcError as e:
        raise HTTPException(status_code=e.code().value[0], detail=e.details())


@app.delete("/posts/{post_id}")
def delete_post(post_id: str):
    try:
        grpc_uuid = post_pb2.UUID(value=post_id)
        response = stub.DeletePost(grpc_uuid)
        return MessageToDict(response)
    except grpc.RpcError as e:
        raise HTTPException(status_code=e.code().value[0], detail=e.details())

@app.get("/openapi.yaml", include_in_schema=False)
def get_openapi_yaml():
    openapi_schema = get_openapi(
        title = "UserService",
        version="1.0.0",
        routes=app.routes
    )
    yaml_schema = yaml.dump(openapi_schema, sort_keys=False, allow_unicode=True)
    return Response(content=yaml_schema, media_type="application/x-yaml")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)