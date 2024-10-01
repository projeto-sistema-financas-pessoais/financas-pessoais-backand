from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional

class UsuarioSchema(BaseModel):
    nome_completo: str
    data_nascimento: datetime
    email: EmailStr
    senha: str

class LoginDataSchema(BaseModel):
    email: EmailStr
    senha: str

class UpdateUsuarioSchema(BaseModel):
    nome_completo: Optional[str] = None
    data_nascimento: Optional[datetime] = None

    class Config:
        orm_mode = True

    