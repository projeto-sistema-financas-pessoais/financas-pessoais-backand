from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional

from models.enums import TipoConta


class ContaSchema(BaseModel):
    descricao: str
    tipo_conta: TipoConta
    nome: str
    nome_icone: str
    ativo : Optional[bool] = True
    
    class Config:
        from_attributes = True
    
    
    
class ContaSchemaUp(ContaSchema):
    descricao: Optional[str] = None
    tipo_conta: Optional[TipoConta]
    nome: Optional[str] = None
    nome_icone: Optional[str] = None
    ativo : Optional[bool] = True