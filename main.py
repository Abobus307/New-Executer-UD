# main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os

app = FastAPI(title="Simple HTTPS -> HTTP proxy")

# SECURITY: разрешённые origins (замени на свой GitHub Pages домен или список доменов)
ALLOWED_ORIGINS = [
    "https://<твой-аккаунт>.github.io",    # <- замените
    # "https://your-custom-domain.com",
]

# Если хочешь разрешить всем (не рекомендую в проде) — используй ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

# Рекомендуется включить API-ключ (чтобы сервис не стал открытым прокси)
API_KEY = os.environ.get("API_KEY")  # задавать в Render Dashboard -> Environment

# Базовые настройки проксирования
TARGET_BASE = "http://farts.fadedis.xyz"  # можно менять
TIMEOUT = 10.0  # seconds

# Небольшая белая часть: разрешённые пути (чтобы не превратить сервис в полный open proxy)
ALLOWED_PATH_PREFIXES = ["/api/status", "/status", "/public"]  # настрой под свои нужды

def is_path_allowed(path: str) -> bool:
    if not ALLOWED_PATH_PREFIXES:
        return True
    for p in ALLOWED_PATH_PREFIXES:
        if path.startswith(p):
            return True
    return False

@app.get("/proxy{full_path:path}")
async def proxy_get(full_path: str, request: Request):
    # Проверка API-ключа (если задан)
    if API_KEY:
        key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
        if key != API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API key")

    # Собираем путь для запроса к целевому HTTP-ресурсу
    # full_path уже начинается с '/', например "/api/status"
    if not is_path_allowed(full_path):
        raise HTTPException(status_code=403, detail="Path not allowed")

    target_url = f"{TARGET_BASE}{full_path}"
    # Пробрасываем query string
    if request.scope.get("query_string"):
        qs = request.scope["query_string"].decode()
        if qs:
            target_url = f"{target_url}?{qs}"

    headers = {"User-Agent": "render-proxy/1.0"}
    # Можно пробросить некоторые заголовки клиента, но не все — осторожно
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(target_url, headers=headers)
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Upstream request failed: {e}")

    # Пробрасываем статус и тело (предположим, чаще всего json или text)
    content_type = resp.headers.get("content-type", "")
    if "application/json" in content_type:
        return JSONResponse(status_code=resp.status_code, content=resp.json())
    else:
        return PlainTextResponse(status_code=resp.status_code, content=resp.text)
