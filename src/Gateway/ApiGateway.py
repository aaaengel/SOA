from fastapi import FastAPI, Request, Response
import uvicorn
import httpx
import logging
import json
import os

app = FastAPI()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

SERVICES = { 
    "user": os.getenv("USER_SERVICE_URL", "http://userservice:5001"),
}

async def handle_req(req: Request, path: str, service: str):
    async with httpx.AsyncClient() as client:
        # Читаем тело запроса (нужно вызывать await req.body() только один раз)
        body = await req.body()

        # Прокидываем заголовки, кроме Host (его ставит сам httpx)
        headers = {k: v for k, v in req.headers.items() if k.lower() != "host"}

        # Отправляем запрос ровно таким же методом
        proxy_resp = await client.request(
            method=req.method,
            url=f"{SERVICES[service]}/{path}",
            params=req.query_params,
            headers=headers,
            content=body  # Используем content, чтобы переслать данные 1-в-1
        )

        # Возвращаем ответ от сервера как есть
        return Response(
            content=proxy_resp.content,
            status_code=proxy_resp.status_code,
            headers=dict(proxy_resp.headers)
        )

@app.get("/favicon.ico")
async def favicon():
    # Можно вернуть пустой ответ, если фавиконка не требуется
    return Response(status_code=204)
@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def hadle(path: str, service: str, request: Request):
    
    return await handle_req(request, path, service)

if __name__ == "__main__":
    uvicorn.run("ApiGateway:app", host="localhost", port=5000, reload=True)