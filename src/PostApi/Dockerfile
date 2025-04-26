FROM python:3.10-slim

WORKDIR /app

COPY PostApi/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

COPY PostApi/ .

COPY proto/ ./proto

RUN python -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. ./proto/post.proto


EXPOSE 8000

CMD ["uvicorn", "Api:app", "--host", "0.0.0.0", "--port", "8000"]
