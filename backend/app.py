"""
Chatbot Financeiro BR — Backend
FastAPI + OpenAI Function Calling + APIs Oficiais Brasileiras
"""
import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routers import chat

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not os.getenv("OPENAI_API_KEY"):
        logging.warning("OPENAI_API_KEY não configurada — o chat não funcionará sem ela.")
    yield


app = FastAPI(
    title="Chatbot Financeiro BR",
    description="API de chatbot financeiro educativo com dados de fontes oficiais brasileiras.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")

# Serve o frontend como arquivos estáticos na raiz
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")


@app.get("/health", tags=["infra"])
async def health():
    return {
        "status": "ok",
        "openai_configurado": bool(os.getenv("OPENAI_API_KEY")),
        "transparencia_configurado": bool(os.getenv("TRANSPARENCIA_API_KEY")),
    }
