from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2 import sql
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta, timezone
import logging
import jwt
from passlib.context import CryptContext


from fastapi import FastAPI

from core.configs import settings
from api.v1.api import api_router

app: FastAPI = FastAPI(title='Finanças Pessoais')
app.include_router(api_router, prefix=settings.API_V1_STR)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todas as origens; ajuste conforme necessário
    allow_methods=["GET", "POST", "PUT", "OPTIONS", "DELETE"],
    allow_headers=["*"],
)



if __name__ == '__main__':
    import uvicorn
    uvicorn.run("main:app", host="localhost", port=9000, log_level="info", reload=True)

