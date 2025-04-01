FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY PostComService/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

COPY PostComService/ .

COPY proto/ ./proto

RUN python -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. ./proto/post.proto

EXPOSE 50051

CMD ["python", "-m", "App.App"]
