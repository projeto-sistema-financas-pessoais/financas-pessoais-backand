from datetime import date
from pydantic import BaseModel, EmailStr
from typing import Optional

class UsuarioSchema(BaseModel):
    nome_completo: str
    data_nascimento: date
    email: EmailStr
    senha: str

class LoginDataSchema(BaseModel):
    email: EmailStr
    senha: str

class UpdateUsuarioSchema(BaseModel):
    nome_completo: Optional[str] = None
    data_nascimento: Optional[date] = None

    class Config:
        from_attributes = True

    