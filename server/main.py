# ============================================================
# Точка входа FastAPI
# ============================================================

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, users, books, readers, rentals
import config
from config import HOST, PORT, SSL_CERT_PATH, SSL_KEY_PATH

app = FastAPI(title="АИС Библиотека")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Роутеры
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(books.router, prefix="/api")
app.include_router(readers.router, prefix="/api")
app.include_router(rentals.router, prefix="/api")


@app.get("/")
def root():
    return {"message": "АИС Библиотека API работает"}


@app.get("/maintenance")
def maintenance_status():
    return {"maintenance": config.MAINTENANCE_MODE}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        ssl_keyfile=SSL_KEY_PATH,
        ssl_certfile=SSL_CERT_PATH,
        reload=False,
    )
