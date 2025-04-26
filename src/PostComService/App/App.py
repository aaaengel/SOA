import grpc
from concurrent import futures
import uuid
from datetime import datetime, timezone
from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf.empty_pb2 import Empty

import post_pb2_grpc as post_pb2_grpc
import post_pb2
from Schemas.schema import Base, Post, PostComment, PostPhoto
from Database.db import SessionLocal, engine
import Crud.crud as crud
import os, json
from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092'),
    value_serializer=lambda v: json.dumps(v, default=str).encode()
)

def datetime_to_timestamp(dt: datetime) -> Timestamp:
    ts = Timestamp()
    ts.FromDatetime(dt)
    return ts


def post_to_proto(post_model: Post):
    proto_post = post_pb2.Post(
        name=post_model.name,
        desc=post_model.desc,
        private=post_model.private,
        tags=post_model.tags,
        uuid=post_pb2.UUID(value=str(post_model.id)),
        uuid_user=post_pb2.UUID(value=str(post_model.user_id)),
    )
    if post_model.created_at:
        proto_post.date.CopyFrom(datetime_to_timestamp(post_model.created_at))
    if post_model.updated_at:
        proto_post.update_date.CopyFrom(datetime_to_timestamp(post_model.updated_at))
    return proto_post

class PostService(post_pb2_grpc.PostsServicer):
    def CreatePost(self, request, context):
        try:
            with SessionLocal() as db:
                crud.create_post_sync(db, request)
            return post_pb2.PostResponse(code=200, message="Post created successfully")
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Ошибка создания поста: {e}")

    def GetById(self, request, context):
        try:
            with SessionLocal() as db:
                post_obj = crud.get_post_by_id_sync(db, uuid.UUID(request.value))
            print(post_obj)
            if not post_obj:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Post not found")
                return
            return post_to_proto(post_obj)
        except Exception as e:
            import traceback
            traceback.print_exc()
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def GetPosts(self, request, context):
        try:
            with SessionLocal() as db:
                posts = crud.get_posts_by_user_id_sync(db, uuid.UUID(request.value))
            for post in posts:
                yield post_to_proto(post)
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def UpdatePost(self, request, context):
        try:
            with SessionLocal() as db:
                updated = crud.update_post_sync(
                    db,
                    uuid.UUID(request.uuid.value),
                    request.name,
                    request.desc,
                    request.tags,
                )
            if not updated:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Post not found")
                return
            return post_pb2.PostResponse(code=200, message="Post updated")
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def DeletePost(self, request, context):
        try:
            with SessionLocal() as db:
                deleted = crud.delete_post_sync(db, uuid.UUID(request.value))
            if not deleted:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Post not found")
                return
            return post_pb2.PostResponse(code=200, message="Deleted")
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def ViewPost(self, request, context):
        post_id = uuid.UUID(request.post_uuid.value)
        user_id = uuid.UUID(request.user_uuid.value)
        with SessionLocal() as db:
            crud.view_post_sync(db, post_id)
        event = {
            'client_id': str(user_id),
            'entity': 'post',
            'entity_id': str(post_id),
            'timestamp':  datetime.now(timezone.utc)
        }
        producer.send('post-views', event)
        producer.flush()
        return Empty()

    def LikePost(self, request, context):
        post_id = uuid.UUID(request.post_uuid.value)
        user_id = uuid.UUID(request.user_uuid.value)
        with SessionLocal() as db:
            crud.like_post_sync(db, post_id)
        event = {
            'client_id': str(user_id),
            'entity': 'post',
            'entity_id': str(post_id),
            'timestamp':  datetime.now(timezone.utc)
        }
        producer.send('post-likes', event)
        producer.flush()
        return Empty()

    def CommentPost(self, request, context):
        post_id = uuid.UUID(request.post_uuid.value)
        user_id = uuid.UUID(request.user_uuid.value)
        with SessionLocal() as db:
            comment = crud.comment_post_sync(
                db, post_id, user_id, request.content,
                uuid.UUID(request.replied.value) if request.replied.value else None
            )
        event = {
            'client_id': str(user_id),
            'entity': 'post',
            'entity_id': str(post_id),
            'comment_id': str(comment.comment_id),
            'timestamp':  datetime.now(timezone.utc)
        }
        producer.send('post-comments', event)
        producer.flush()
        return post_pb2.CommentResponse(comment_id=post_pb2.UUID(value=str(comment.comment_id)))

    def GetComments(self, request, context):
        post_id = uuid.UUID(request.post_uuid.value)
        page = request.page
        size = request.size
        offset = (page - 1) * size
        with SessionLocal() as db:
            comments = crud.get_comments_paginated_sync(db, post_id, offset, size)
        response = post_pb2.GetCommentsResponse()
        for c in comments:
            msg = post_pb2.Comment(
                comment_id=post_pb2.UUID(value=str(c.comment_id)),
                commenter_id=post_pb2.UUID(value=str(c.commenter_id)),
                content=c.content,
            )
            msg.posted_at.CopyFrom(datetime_to_timestamp(c.posted_at))
            if c.replied:
                msg.replied.CopyFrom(post_pb2.UUID(value=str(c.replied)))
            response.comments.append(msg)
        return response

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    post_pb2_grpc.add_PostsServicer_to_server(PostService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("gRPC server running on [::]:50051")
    server.wait_for_termination()

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    serve()
