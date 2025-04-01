from datetime import datetime, timedelta, timezone
import post_pb2 as post_pb2
import post_pb2_grpc as post_pb2_grpc
from concurrent import futures
import grpc
import Crud.crud as crud
from sqlalchemy.ext.asyncio import AsyncSession
from google.protobuf.timestamp_pb2 import Timestamp
from Database.db import SessionLocal, engine
from Schemas.schema import Base, Post
import asyncio
from google.protobuf.json_format import MessageToDict
import uuid

async def create_tables():
    async with engine.begin() as conn:
        print(Base.metadata)
        await conn.run_sync(Base.metadata.create_all)

def datetime_to_timestamp(dt: "datetime") -> Timestamp:
    ts = Timestamp()
    ts.FromDatetime(dt)
    return ts
    
def post_to_proto(post_model: Post):
    proto_post = post_pb2.Post(
        name=post_model.name or "",
        desc=post_model.desc or "",
        private=post_model.private,
        tags=post_model.tags or [],
        uuid=post_pb2.UUID(value=str(post_model.id)),
        uuid_user=post_pb2.UUID(value=str(post_model.user_id))
    )
    if post_model.created_at:
        proto_post.date.CopyFrom(datetime_to_timestamp(post_model.created_at))
    if post_model.updated_at:
        proto_post.update_date.CopyFrom(datetime_to_timestamp(post_model.updated_at))
    return proto_post

class Post(post_pb2_grpc.PostsServicer):
    def CreatePost(self, request, context):
        try:
            async def _create():
                async with SessionLocal() as db:
                    return await crud.create_post(db, request)
            created_post = asyncio.run(_create())
            created = asyncio.run(crud.create_post())
            return post_pb2.PostResponse(
                code=200,
                message="Post created successfully"
            )
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Ошибка создания поста: {str(e)}")
        
    def GetById(self, request, context):
        try:
            async def _get_by_id():
                async with SessionLocal() as db:
                    return await crud.get_post_by_id(db, uuid.UUID(request.value))
            post_obj = asyncio.run(_get_by_id())
            if not post_obj:
                context.abort(grpc.StatusCode.NOT_FOUND, "Post not found")
            return post_to_proto(post_obj)
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Ошибка получения поста: {str(e)}")
    def GetPosts(self, request, context):
        try:
            async def _get_posts():
                async with SessionLocal() as db:
                    return await crud.get_posts_by_user_id(db, uuid.UUID(request.value))
            posts_list = asyncio.run(_get_posts())
            for post_obj in posts_list:
                yield post_to_proto(post_obj)
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Ошибка получения постов: {str(e)}")
    def UpdatePost(self, request, context):
        try:
            async def _update():
                async with SessionLocal() as db:
                    post_id = uuid.UUID(request.uuid.value)
                    updated_post = await crud.update_post(
                        db,
                        post_id,
                        name=request.name if request.name else None,
                        desc=request.desc if request.desc else None,
                        tags=request.tags if request.tags else None
                    )
                    if not updated_post:
                        context.abort(grpc.StatusCode.NOT_FOUND, "Post not found")
                    return updated_post

            updated_post = asyncio.run(_update())
            return post_pb2.PostResponse(
                code=200,
                message="Post updated successfully"
            )
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Ошибка обновления поста: {str(e)}")
    def DeletePost(self, request, context):
        try:
            async def _delete():
                async with SessionLocal() as db:
                    post_id = uuid.UUID(request.value)
                    deleted = crud.delete_post(post_id)
                    if not deleted:
                        context.abort(grpc.StatusCode.NOT_FOUND, "Post not found")
            asyncio.run(_delete())
            return post_pb2.PostResponse(
                code=200,
                message="Post deleted successfully"
            )
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Ошибка удаления поста: {str(e)}")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    post_pb2_grpc.add_PostsServicer_to_server(Post, server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination(timeout=None)

if __name__ == "__main__":
    serve()