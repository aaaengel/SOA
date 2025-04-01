from fastapi import FastAPI, Request, Depends, status, HTTPException, Response
import uvicorn
import httpx
import logging
import os
import jwt
from datetime import datetime, timedelta, timezone

app = FastAPI()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

ALGORITHM = "RS256"
with open("private.pem", "rb") as f:
    PRIVATE_KEY = f.read()
with open("public.pem", "rb") as f:
    PUBLIC_KEY = f.read()

SERVICES = { 
    "user": os.getenv("USER_SERVICE_URL", "http://userservice:5001"),
    "post": os.getenv("POST_SERVICE_URL", "http://postapi:8000")
}
def verify_access_token(token: str):
    try:
        print(PUBLIC_KEY)
        payload = jwt.decode(token, PUBLIC_KEY, algorithm=ALGORITHM)
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token')

def get_token(request: Request):
    token = request.cookies.get('token')
    print(token)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token not found')
    return token

    
async def get_current_user(token: str = Depends(get_token)):
    payload = verify_access_token(token)
    expire = payload.get('exp')
    expire_time = datetime.fromtimestamp(int(expire), tz=timezone.utc)
    if (not expire) or (expire_time < datetime.now(timezone.utc)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Токен истек')

    user_id = payload.get('id')
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='No id provided')

    return user_id


@app.api_route("/{service}/{path:path}", methods=["GET","POST","PUT","DELETE","PATCH","OPTIONS","HEAD"])
async def main_proxy(req: Request, service: str, path: str):
    return await handle_req(req, path, service)

async def handle_req(req: Request, path: str, service: str):
    async with httpx.AsyncClient() as client:
        body = await req.body()
        headers = {k: v for k, v in req.headers.items() if k.lower() != "host"}
        if service == 'post':
            id = await get_current_user()
            me_resp = await client.request(
                method="GET",
                url=f"{SERVICES['user']}/me",
                headers=headers
            )
            if me_resp.status_code != 200:
                raise HTTPException(status_code=401, detail="Unauthorized")

            user_data = me_resp.json()
            if str(id) != str(user_data["id"]):
                raise HTTPException(status_code=403, detail="Wrong user")
        cookies = req.cookies
        print(cookies)
        proxy_resp = await client.request(
            method=req.method,
            url=f"{SERVICES[service]}/{path}",
            params=req.query_params,
            headers=headers,
            content=body,
            cookies=cookies
        )

        return Response(
            content=proxy_resp.content,
            status_code=proxy_resp.status_code,
            headers=dict(proxy_resp.headers)
        )

if __name__ == "__main__":
    uvicorn.run("ApiGateway:app", host="localhost", port=5000, reload=True)