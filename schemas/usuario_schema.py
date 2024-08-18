

from datetime import datetime
from pydantic import BaseModel, EmailStr


class UsuarioSchema(BaseModel):
    nome_completo: str
    data_nascimento: datetime
    email: EmailStr
    senha: str

class LoginDataSchema(BaseModel):
    email: EmailStr
    senha: str
    
    