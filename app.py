from fastapi import FastAPI, HTTPException
import psycopg2
from psycopg2 import sql

# Conectar ao banco de dados PostgreSQL
conn = psycopg2.connect(
    dbname="SCFP",
    user="postgres",
    password="3003",
    host="localhost"
)
cur = conn.cursor()

app = FastAPI()


@app.post("/clientes/")
async def cadastrar_cliente(cpf: int, nome_completo: str, data_nascimento: str, email: str, senha: str):
    try:
        cur.execute(
            sql.SQL("INSERT INTO cliente (cpf, nome_completo, data_nascimento, email, senha) VALUES (%s, %s, %s, %s, %s)"),
            (cpf, nome_completo, data_nascimento, email, senha)
        )
        conn.commit()
        return {"mensagem": "Cliente cadastrado com sucesso"}
    except psycopg2.IntegrityError as e:
        if "duplicate key value" in str(e):
            raise HTTPException(status_code=409, detail="CPF já cadastrado")
        else:
            raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.get("/scfp/{cpf}")
async def obter_cliente(cpf: int):
    cur.execute(
        sql.SQL("SELECT * FROM cliente WHERE cpf = %s"),
        (cpf,)
    )
    cliente = cur.fetchone()
    if cliente:
        return {
            "nome_completo": cliente[0],
            "data_nascimento": cliente[1],
            "cpf": cliente[2],
            "email": cliente[3],
            "senha": cliente[4]
        }
    else:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
