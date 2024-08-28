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
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# # Configurar logging
# logging.basicConfig(level=logging.INFO)

# # Configurar senha
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# # Configurar JWT
# SECRET_KEY = "your_secret_key"
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 30

# # Conectar ao banco de dados PostgreSQL
# conn = psycopg2.connect(
#     dbname="SCFP",
#     user="postgres",
#     password="3003",
#     host="localhost"
# )
# cur = conn.cursor()

# app = FastAPI()

# # Configuração do middleware CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["GET", "POST", "OPTIONS"],
#     allow_headers=["*"],
# )

# class Cliente(BaseModel):
#     nome_completo: str
#     data_nascimento: datetime
#     email: EmailStr
#     senha: str

# class LoginData(BaseModel):
#     email: EmailStr
#     senha: str

# @app.post("/auth/register/")
# async def register_client(cliente: Cliente):
#     hashed_password = pwd_context.hash(cliente.senha)
#     try:
#         cur.execute(
#             sql.SQL("INSERT INTO cliente (nome_completo, data_nascimento, email, senha) VALUES (%s, %s, %s, %s)"),
#             (cliente.nome_completo, cliente.data_nascimento, cliente.email, hashed_password)
#         )
#         conn.commit()
#         return {"mensagem": "Cliente cadastrado com sucesso"}
#     except psycopg2.IntegrityError as e:
#         conn.rollback()
#         logging.error(f"IntegrityError: {str(e)}")
#         raise HTTPException(status_code=409, detail="Email já existe")
#     except Exception as e:
#         conn.rollback()
#         logging.error(f"Exception: {str(e)}")
#         raise HTTPException(status_code=500, detail="Erro interno do servidor")

# @app.post("/auth/login/")
# async def login(login_data: LoginData):
#     try:
#         cur.execute(
#             sql.SQL("SELECT nome_completo, senha FROM cliente WHERE email = %s"),
#             (login_data.email,)
#         )
#         cliente = cur.fetchone()
#         if not cliente:
#             raise HTTPException(status_code=401, detail="Email ou senha incorretos")

#         nome_completo, senha_hash = cliente

#         if not pwd_context.verify(login_data.senha, senha_hash):
#             raise HTTPException(status_code=401, detail="Email ou senha incorretos")

#         access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#         access_token = create_access_token(
#             data={"sub": login_data.email, "nome": nome_completo}, expires_delta=access_token_expires
#         )

#         return {"nome": nome_completo, "acesso_token": access_token}
#     except Exception as e:
#         logging.error(f"Exception: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}")

# def create_access_token(data: dict, expires_delta: timedelta = None):
#     to_encode = data.copy()
#     if expires_delta:
#         expire = datetime.now(timezone.utc) + expires_delta
#     else:
#         expire = datetime.now(timezone.utc) + timedelta(minutes=15)
#     to_encode.update({"exp": expire})
#     encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
#     return encoded_jwt

# @app.get("/clients/{email}")
# async def get_client(email: str):
#     try:
#         cur.execute(
#             sql.SQL("SELECT * FROM cliente WHERE email = %s"),
#             (email,)
#         )
#         cliente = cur.fetchone()
#         if cliente:
#             return {
#                 "nome_completo": cliente[0],
#                 "data_nascimento": cliente[1],
#                 "email": cliente[2],
#                 "senha": cliente[3]
#             }
#         else:
#             raise HTTPException(status_code=404, detail="Cliente não encontrado")
#     except Exception as e:
#         logging.error(f"Exception: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}")

# @app.get("/clients/")
# async def get_all_clients():
#     try:
#         cur.execute(
#             sql.SQL("SELECT nome_completo, data_nascimento, email FROM cliente")
#         )
#         clientes = cur.fetchall()
#         return [
#             {
#                 "nome_completo": cliente[0],
#                 "data_nascimento": cliente[1],
#                 "email": cliente[2]
#             } for cliente in clientes
#         ]
#     except Exception as e:
#         logging.error(f"Exception: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}")


if __name__ == '__main__':
    import uvicorn
    uvicorn.run("main:app", host="localhost", port=9000, log_level="info", reload=True)

