from datetime import datetime
from pydantic import BaseModel, EmailStr


class ContaSchema(BaseModel):
    descricao: str
    tipo_conta: str
    nome: str
    nome_icone: str